#!/usr/bin/env python3
"""
Smart Smokehouse - Raspberry Pi Bridge
Odbiera dane z AWS IoT Cloud i przekazuje do ESP32 via local MQTT
Obsługuje przycisk GPIO do startowania procesu wędzenia
"""

import ssl
import json
import time
import os
import struct
import threading
from enum import IntEnum
from paho.mqtt import client as mqtt

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("⚠️  RPi.GPIO not available - button functionality disabled")
    GPIO_AVAILABLE = False

# ============================================================================
# AWS IoT Configuration (Cloud Input)
# ============================================================================
IOT_ENDPOINT = "apc4udnp426oi-ats.iot.eu-central-1.amazonaws.com"
IOT_PORT = 8883
IOT_TOPIC = "decoded/#"
IOT_CLIENT_ID = "raspberrypi-smokehouse-bridge"

CERT_ROOT = os.path.expanduser("~/iot/certs/AmazonRootCA1.pem")
CERT_FILE = os.path.expanduser("~/iot/certs/f397c6ef30d1506986fcfb78b23d519599e830bf5e15f66132f5f5cb678cd99c-certificate.pem.crt")
KEY_FILE = os.path.expanduser("~/iot/certs/f397c6ef30d1506986fcfb78b23d519599e830bf5e15f66132f5f5cb678cd99c-private.pem.key")

# ============================================================================
# Local MQTT Configuration (ESP32 Output)
# ============================================================================
LOCAL_MQTT_SERVER = "192.168.0.106"
LOCAL_MQTT_PORT = 1883
LOCAL_TOPIC_START = "robot/frame/start"
LOCAL_TOPIC_UPDATE = "robot/frame/"
LOCAL_TOPIC_STATE = "robot/state"

# ============================================================================
# GPIO Configuration (Button)
# ============================================================================
BUTTON_PIN = 17  # GPIO17 (Pin 11 na Raspberry Pi)
# Podłączenie przycisku:
# - Jeden koniec przycisku → GPIO17 (Pin 11)
# - Drugi koniec → GND (Pin 9, 14, 20, 25, 30, 34, lub 39)
# - GPIO17 będzie miał wewnętrzny pull-up, więc przycisk zwiera do GND

# ============================================================================
# Frame Configuration (matching ESP32)
# ============================================================================
class FrameType(IntEnum):
    NO_NEW_FRAME = 0
    START_FRAME = 1
    UPDATE_FRAME = 2

MEAT_NAME_LENGTH = 30

# START_FRAME positions
START_FRAME_COMMAND_VALUE_PLACE = 1
START_FRAME_MEAT_NAME_PLACE = START_FRAME_COMMAND_VALUE_PLACE + 1
START_FRAME_TARGET_HUMIDITY_PLACE = START_FRAME_MEAT_NAME_PLACE + MEAT_NAME_LENGTH
START_FRAME_TARGET_TEMPERATURE_PLACE = START_FRAME_TARGET_HUMIDITY_PLACE + 1
START_FRAME_CURRENT_HUMIDITY_PLACE = START_FRAME_TARGET_TEMPERATURE_PLACE + 2
START_FRAME_CURRENT_TEMPERATURE_PLACE = START_FRAME_CURRENT_HUMIDITY_PLACE + 1
START_FRAME_DOOR_STATUS_PLACE = START_FRAME_CURRENT_TEMPERATURE_PLACE + 2
START_FRAME_TIME_OF_SMOKING_PLACE = START_FRAME_DOOR_STATUS_PLACE + 1

# UPDATE_FRAME positions
UPDATE_FRAME_CURRENT_HUMIDITY_PLACE = 1
UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE = UPDATE_FRAME_CURRENT_HUMIDITY_PLACE + 1
UPDATE_FRAME_DOOR_STATUS_PLACE = UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE + 2

# ============================================================================
# Global State
# ============================================================================
class SmokehouseState:
    """Przechowuje aktualny stan wędzarni"""
    def __init__(self):
        self.temperature = 230  # 23.0°C (format: °C * 10)
        self.humidity = 45      # 45%
        self.door_status = 0    # 0=closed, 1=open
        self.last_update = time.time()
        self.esp_state = "UNKNOWN"
        
        # Parametry procesu wędzenia (ustawiane przyciskiem)
        self.target_temperature = 650   # 65.0°C
        self.target_humidity = 75       # 75%
        self.smoking_duration = 20      # 20 sekund
        self.meat_name = "Boczek"
        
        self.lock = threading.Lock()

state = SmokehouseState()

# ============================================================================
# MQTT Frame Creation Functions
# ============================================================================

def create_start_frame(command, meat_name, target_humidity, target_temperature,
                       current_humidity, current_temperature, door_status, time_of_smoking):
    """Tworzy START_FRAME dla ESP32"""
    total_size = START_FRAME_TIME_OF_SMOKING_PLACE + 2
    payload = bytearray(total_size)
    
    payload[0] = FrameType.START_FRAME
    payload[START_FRAME_COMMAND_VALUE_PLACE] = command & 0xFF
    
    # Meat name
    meat_bytes = meat_name.encode('utf-8')[:MEAT_NAME_LENGTH]
    for i in range(min(len(meat_bytes), MEAT_NAME_LENGTH)):
        payload[START_FRAME_MEAT_NAME_PLACE + i] = meat_bytes[i]
    
    # Target values
    payload[START_FRAME_TARGET_HUMIDITY_PLACE] = target_humidity & 0xFF
    temp_bytes = struct.pack('<h', target_temperature)
    payload[START_FRAME_TARGET_TEMPERATURE_PLACE:START_FRAME_TARGET_TEMPERATURE_PLACE+2] = temp_bytes
    
    # Current values
    payload[START_FRAME_CURRENT_HUMIDITY_PLACE] = current_humidity & 0xFF
    curr_temp_bytes = struct.pack('<h', current_temperature)
    payload[START_FRAME_CURRENT_TEMPERATURE_PLACE:START_FRAME_CURRENT_TEMPERATURE_PLACE+2] = curr_temp_bytes
    
    # Door and time
    payload[START_FRAME_DOOR_STATUS_PLACE] = door_status & 0xFF
    time_bytes = struct.pack('<H', time_of_smoking)
    payload[START_FRAME_TIME_OF_SMOKING_PLACE:START_FRAME_TIME_OF_SMOKING_PLACE+2] = time_bytes
    
    return payload

def create_update_frame(current_humidity, current_temperature, door_status):
    """Tworzy UPDATE_FRAME dla ESP32"""
    total_size = UPDATE_FRAME_DOOR_STATUS_PLACE + 1
    payload = bytearray(total_size)
    
    payload[0] = FrameType.UPDATE_FRAME
    payload[UPDATE_FRAME_CURRENT_HUMIDITY_PLACE] = current_humidity & 0xFF
    
    temp_bytes = struct.pack('<h', current_temperature)
    payload[UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE:UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE+2] = temp_bytes
    
    payload[UPDATE_FRAME_DOOR_STATUS_PLACE] = door_status & 0xFF
    
    return payload

# ============================================================================
# Local MQTT Client (ESP32)
# ============================================================================

class LocalMQTTClient:
    """Klient MQTT do komunikacji z ESP32"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id="rpi-bridge-local")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✓ Połączono z lokalnym MQTT brokerem ({LOCAL_MQTT_SERVER}:{LOCAL_MQTT_PORT})")
            client.subscribe(LOCAL_TOPIC_STATE)
            print(f"✓ Subskrybowano '{LOCAL_TOPIC_STATE}' (stany ESP32)")
            self.connected = True
        else:
            print(f"✗ Błąd połączenia z lokalnym brokerem, rc={rc}")
    
    def on_message(self, client, userdata, msg):
        """Odbiera stany z ESP32"""
        if msg.topic == LOCAL_TOPIC_STATE:
            esp_state = msg.payload.decode('utf-8')
            with state.lock:
                old_state = state.esp_state
                state.esp_state = esp_state
            
            if esp_state != old_state:
                print(f"\n{'='*70}")
                print(f"📥 ESP32 STATE: {old_state} → {esp_state}")
                print(f"{'='*70}\n")
    
    def connect(self):
        try:
            print(f"Łączenie z lokalnym MQTT brokerem {LOCAL_MQTT_SERVER}:{LOCAL_MQTT_PORT}...")
            self.client.connect(LOCAL_MQTT_SERVER, LOCAL_MQTT_PORT, 60)
            self.client.loop_start()
            time.sleep(2)
            return True
        except Exception as e:
            print(f"✗ Błąd połączenia z lokalnym brokerem: {e}")
            return False
    
    def publish_start_frame(self):
        """Wysyła START_FRAME do ESP32"""
        with state.lock:
            payload = create_start_frame(
                command=1,
                meat_name=state.meat_name,
                target_humidity=state.target_humidity,
                target_temperature=state.target_temperature,
                current_humidity=state.humidity,
                current_temperature=state.temperature,
                door_status=state.door_status,
                time_of_smoking=state.smoking_duration
            )
        
        print(f"\n📤 Wysyłanie START_FRAME do ESP32")
        print(f"  Mięso: {state.meat_name}")
        print(f"  Target - Temp: {state.target_temperature/10:.1f}°C, Wilgotność: {state.target_humidity}%")
        print(f"  Current - Temp: {state.temperature/10:.1f}°C, Wilgotność: {state.humidity}%")
        print(f"  Drzwi: {'OTWARTE' if state.door_status else 'ZAMKNIĘTE'}")
        print(f"  Czas: {state.smoking_duration}s\n")
        
        self.client.publish(LOCAL_TOPIC_START, payload, qos=1)
    
    def publish_update_frame(self):
        """Wysyła UPDATE_FRAME do ESP32"""
        with state.lock:
            payload = create_update_frame(
                current_humidity=state.humidity,
                current_temperature=state.temperature,
                door_status=state.door_status
            )
        
        print(f"📤 UPDATE: Temp={state.temperature/10:.1f}°C, Wilg={state.humidity}%, Drzwi={'OTWARTE' if state.door_status else 'ZAMKNIĘTE'}")
        
        self.client.publish(LOCAL_TOPIC_UPDATE, payload, qos=1)
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

local_mqtt = LocalMQTTClient()

# ============================================================================
# AWS IoT Client (Cloud)
# ============================================================================

def on_cloud_connect(client, userdata, flags, rc):
    """Callback po połączeniu z AWS IoT"""
    if rc == 0:
        print(f"✓ Połączono z AWS IoT Cloud ({IOT_ENDPOINT})")
        client.subscribe(IOT_TOPIC)
        print(f"✓ Subskrybowano '{IOT_TOPIC}' (czujniki z chmury)")
    else:
        print(f"✗ Błąd połączenia z AWS IoT, rc={rc}")

def on_cloud_message(client, userdata, msg):
    """Odbiera dane z AWS IoT i aktualizuje stan"""
    try:
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)
        
        # Sprawdź czy to czujnik temperatury/wilgotności
        if "data" in data:
            sensor_data = data["data"]
            
            # Czujnik temperatury/wilgotności
            if "temperature" in sensor_data and "humidity" in sensor_data:
                temp_celsius = sensor_data["temperature"]
                humidity_percent = sensor_data["humidity"]
                
                # Konwertuj do formatu ESP32 (temperatura * 10)
                temp_esp_format = int(temp_celsius * 10)
                humidity_esp_format = int(humidity_percent)
                
                with state.lock:
                    state.temperature = temp_esp_format
                    state.humidity = humidity_esp_format
                    state.last_update = time.time()
                
                print(f"☁️  Temp: {temp_celsius:.1f}°C, Wilg: {humidity_percent:.1f}% (z chmury)")
                
                # Wyślij UPDATE_FRAME do ESP32
                if local_mqtt.connected:
                    local_mqtt.publish_update_frame()
            
            # Czujnik drzwi
            if "door_open_status" in sensor_data:
                door_open = sensor_data["door_open_status"]
                
                with state.lock:
                    state.door_status = door_open
                    state.last_update = time.time()
                
                print(f"🚪 Drzwi: {'OTWARTE' if door_open else 'ZAMKNIĘTE'} (z chmury)")
                
                # Wyślij UPDATE_FRAME do ESP32
                if local_mqtt.connected:
                    local_mqtt.publish_update_frame()
        
    except json.JSONDecodeError as e:
        print(f"⚠️  Błąd parsowania JSON: {e}")
    except Exception as e:
        print(f"⚠️  Błąd przetwarzania wiadomości: {e}")

def setup_cloud_client():
    """Konfiguruje i łączy z AWS IoT"""
    client = mqtt.Client(client_id=IOT_CLIENT_ID)
    client.tls_set(ca_certs=CERT_ROOT,
                   certfile=CERT_FILE,
                   keyfile=KEY_FILE,
                   tls_version=ssl.PROTOCOL_TLSv1_2)
    client.on_connect = on_cloud_connect
    client.on_message = on_cloud_message
    
    print(f"Łączenie z AWS IoT: {IOT_ENDPOINT}...")
    client.connect(IOT_ENDPOINT, IOT_PORT, keepalive=60)
    return client

# ============================================================================
# GPIO Button Handling
# ============================================================================

def check_button():
    """Sprawdza stan przycisku (polling)"""
    if not GPIO_AVAILABLE:
        return False
    
    try:
        return GPIO.input(BUTTON_PIN) == 0  # LOW = naciśnięty (zwięzany do GND)
    except:
        return False

def handle_button_press():
    """Obsługuje naciśnięcie przycisku"""
    print("\n" + "="*70)
    print("🔴 PRZYCISK NACIŚNIĘTY - Rozpoczynam proces wędzenia!")
    print("="*70)
    
    if local_mqtt.connected:
        local_mqtt.publish_start_frame()
        print("✓ START_FRAME wysłany do ESP32")
    else:
        print("✗ Brak połączenia z lokalnym brokerem MQTT!")
    
    print("="*70 + "\n")

def setup_gpio():
    """Konfiguruje GPIO dla przycisku"""
    if not GPIO_AVAILABLE:
        print("⚠️  GPIO niedostępne - przycisk nie będzie działał")
        return False
    
    try:
        GPIO.setwarnings(False)  # Wyłącz ostrzeżenia
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        print(f"✓ GPIO skonfigurowane: Przycisk na GPIO{BUTTON_PIN} (Pin 11)")
        print(f"  Podłączenie: GPIO{BUTTON_PIN} ←→ Przycisk ←→ GND")
        print(f"  Metoda: Polling (sprawdzanie co 100ms)")
        return True
    except Exception as e:
        print(f"✗ Błąd konfiguracji GPIO: {e}")
        print(f"  Spróbuj uruchomić z sudo: sudo python3 {__file__}")
        return False

# ============================================================================
# Main Program
# ============================================================================

def main():
    print("\n" + "="*70)
    print("Smart Smokehouse - Raspberry Pi Bridge")
    print("="*70)
    print("Funkcje:")
    print("  • Odbiera dane z AWS IoT Cloud (temperatura, wilgotność, drzwi)")
    print("  • Wysyła UPDATE_FRAME do ESP32 (lokalny MQTT)")
    print(f"  • Przycisk GPIO{BUTTON_PIN} wysyła START_FRAME")
    print("="*70 + "\n")
    
    # Konfiguruj GPIO
    gpio_ok = setup_gpio()
    
    # Połącz z lokalnym MQTT (ESP32)
    if not local_mqtt.connect():
        print("✗ Nie można uruchomić bez połączenia z lokalnym brokerem!")
        return
    
    # Połącz z AWS IoT Cloud
    try:
        cloud_client = setup_cloud_client()
        cloud_client.loop_start()  # Start w osobnym wątku
        
        print("\n" + "="*70)
        print("✓ System uruchomiony i gotowy!")
        print("="*70)
        if gpio_ok:
            print(f"🔴 Przycisk na GPIO{BUTTON_PIN} gotowy - naciśnij aby rozpocząć wędzenie")
        print("☁️  Dane z czujników będą automatycznie przekazywane do ESP32")
        print("📡 Stan połączeń: AWS IoT ✓ | Lokalny MQTT ✓")
        print("\nNaciśnij Ctrl+C, aby zakończyć")
        print("="*70 + "\n")
        
        # Główna pętla - sprawdzanie przycisku
        last_button_state = False  # False = nie naciśnięty, True = naciśnięty
        button_press_time = 0
        
        while True:
            if gpio_ok:
                current_button_state = check_button()  # True = naciśnięty (LOW)
                
                # Wykryj naciśnięcie (False → True, czyli zmiana z nie naciśnięty na naciśnięty)
                if current_button_state and not last_button_state:
                    # Debounce - sprawdź czy przycisk jest nadal naciśnięty przez 100ms
                    time.sleep(0.1)
                    if check_button():
                        handle_button_press()
                        button_press_time = time.time()
                        
                        # Czekaj aż przycisk zostanie puszczony (aby uniknąć wielokrotnego wywołania)
                        while check_button():
                            time.sleep(0.05)
                
                last_button_state = current_button_state
            
            time.sleep(0.1)  # Sprawdzaj co 100ms
        
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Zamykanie programu...")
        print("="*70)
    except Exception as e:
        print(f"\n✗ Błąd: {e}")
    finally:
        # Cleanup
        local_mqtt.disconnect()
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        print("✓ Program zakończony\n")

if __name__ == "__main__":
    main()
