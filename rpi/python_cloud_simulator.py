#!/usr/bin/env python3
"""
MQTT Client for Smart Smokehouse - Python Cloud Simulator
Publishes START_FRAME and UPDATE_FRAME messages to ESP32
Subscribes to robot/state to receive ESP32 state machine updates
"""

import paho.mqtt.client as mqtt
import struct
import time
from enum import IntEnum

# MQTT Configuration
#MQTT_SERVER = "192.168.0.157"
MQTT_SERVER = "192.168.0.106"
MQTT_PORT = 1883
MQTT_TOPIC_START = "robot/frame/start"
MQTT_TOPIC_UPDATE = "robot/frame/"
MQTT_TOPIC_STATE = "robot/state"  # Topic do odbierania stanów z ESP32

# Frame Types
class FrameType(IntEnum):
    NO_NEW_FRAME = 0
    START_FRAME = 1
    UPDATE_FRAME = 2

# Constants matching your ESP32 code
MEAT_NAME_LENGTH = 30

# START_FRAME payload positions
# UPDATED TO MATCH globals.hpp!
# payload[0] = Frame type (START_FRAME or UPDATE_FRAME)
# Then data starts at position 1
START_FRAME_COMMAND_VALUE_PLACE = 1  # Command at position 1 (uint8)
START_FRAME_MEAT_NAME_PLACE = START_FRAME_COMMAND_VALUE_PLACE + 1  # char[30] at position 2
START_FRAME_TARGET_HUMIDITY_PLACE = START_FRAME_MEAT_NAME_PLACE + MEAT_NAME_LENGTH  # uint8 at position 32
START_FRAME_TARGET_TEMPERATURE_PLACE = START_FRAME_TARGET_HUMIDITY_PLACE + 1  # int16 at position 33 (2 bytes)
START_FRAME_CURRENT_HUMIDITY_PLACE = START_FRAME_TARGET_TEMPERATURE_PLACE + 2  # uint8 at position 35
START_FRAME_CURRENT_TEMPERATURE_PLACE = START_FRAME_CURRENT_HUMIDITY_PLACE + 1  # int16 at position 36 (2 bytes)
START_FRAME_DOOR_STATUS_PLACE = START_FRAME_CURRENT_TEMPERATURE_PLACE + 2  # uint8 at position 38
START_FRAME_TIME_OF_SMOKING_PLACE = START_FRAME_DOOR_STATUS_PLACE + 1  # uint16 at position 39 (2 bytes)

# UPDATE_FRAME payload positions
# UPDATED to match your corrected ESP32 constants!
# payload[0] = Frame type (UPDATE_FRAME)
# Then data starts at position 1
UPDATE_FRAME_CURRENT_HUMIDITY_PLACE = 1  # uint8 at position 1
UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE = UPDATE_FRAME_CURRENT_HUMIDITY_PLACE + 1  # int16 at position 2 (2 bytes!)
UPDATE_FRAME_DOOR_STATUS_PLACE = UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE + 2  # uint8 at position 4


class MQTTSmokehouseClient:
    """MQTT client for controlling the smokehouse"""

    def __init__(self, broker_address=MQTT_SERVER, port=MQTT_PORT):
        self.broker_address = broker_address
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message

        # Przechowuj ostatni stan z ESP32
        self.last_state = "UNKNOWN"
        self.state_history = []

    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT Broker at {self.broker_address}:{self.port}")
            # Subskrybuj topic ze stanami z ESP32
            client.subscribe(MQTT_TOPIC_STATE)
            print(f"✓ Subscribed to '{MQTT_TOPIC_STATE}' (receiving ESP32 states)")
        else:
            print(f"✗ Connection failed with code {rc}")

    def on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        pass  # Ciche publikowanie, żeby nie zaśmiecać outputu

    def on_message(self, client, userdata, msg):
        """Callback when message is received from ESP32"""
        topic = msg.topic

        if topic == MQTT_TOPIC_STATE:
            # Odbieramy stan maszyny z ESP32
            state = msg.payload.decode('utf-8')

            # Tylko wyświetl jeśli stan się zmienił
            if state != self.last_state:
                print(f"\n{'='*70}")
                print(f"📥 ESP32 STATE CHANGED: {self.last_state} → {state}")
                print(f"{'='*70}\n")

                self.last_state = state
                self.state_history.append(state)
        else:
            print(f"\n📥 Received on '{topic}': {msg.payload}")

    def connect(self):
        """Connect to the MQTT broker"""
        try:
            print(f"Connecting to MQTT broker {self.broker_address}:{self.port}...")
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start()
            time.sleep(1)  # Give time to establish connection
            return True
        except Exception as e:
            print(f"✗ Error connecting to broker: {e}")
            return False

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print("\n✓ Disconnected from MQTT broker")

    def create_start_frame(self, command, meat_name, target_humidity, target_temperature,
                          current_humidity, current_temperature, door_status, time_of_smoking):
        """
        Create START_FRAME payload

        Args:
            command (int): Command value (uint8)
            meat_name (str): Name of meat (max 30 chars)
            target_humidity (int): Target humidity % (uint8)
            target_temperature (int): Target temperature in °C*10 (int16)
            current_humidity (int): Current humidity % (uint8)
            current_temperature (int): Current temperature in °C*10 (int16)
            door_status (int): Door status 0=closed, 1=open (uint8)
            time_of_smoking (int): Time in seconds (uint16)

        Returns:
            bytearray: The frame payload
        """
        # Calculate total size (time_of_smoking is at the end and takes 2 bytes)
        total_size = START_FRAME_TIME_OF_SMOKING_PLACE + 2
        payload = bytearray(total_size)

        # [0] Frame type identifier
        payload[0] = FrameType.START_FRAME

        # [1] Command value (uint8)
        payload[START_FRAME_COMMAND_VALUE_PLACE] = command & 0xFF

        # [2-31] Meat name (char[30])
        meat_bytes = meat_name.encode('utf-8')[:MEAT_NAME_LENGTH]
        for i in range(min(len(meat_bytes), MEAT_NAME_LENGTH)):
            payload[START_FRAME_MEAT_NAME_PLACE + i] = meat_bytes[i]

        # [32] Target humidity (uint8)
        payload[START_FRAME_TARGET_HUMIDITY_PLACE] = target_humidity & 0xFF

        # [33-34] Target temperature (int16, 2 bytes, little-endian)
        temp_bytes = struct.pack('<h', target_temperature)
        payload[START_FRAME_TARGET_TEMPERATURE_PLACE] = temp_bytes[0]
        payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1] = temp_bytes[1]

        # [35] Current humidity (uint8)
        payload[START_FRAME_CURRENT_HUMIDITY_PLACE] = current_humidity & 0xFF

        # [36-37] Current temperature (int16, 2 bytes, little-endian)
        curr_temp_bytes = struct.pack('<h', current_temperature)
        payload[START_FRAME_CURRENT_TEMPERATURE_PLACE] = curr_temp_bytes[0]
        payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1] = curr_temp_bytes[1]

        # [38] Door status (uint8)
        payload[START_FRAME_DOOR_STATUS_PLACE] = door_status & 0xFF

        # [39-40] Time of smoking (uint16, 2 bytes, little-endian) - moved after door_status
        time_bytes = struct.pack('<H', time_of_smoking)
        payload[START_FRAME_TIME_OF_SMOKING_PLACE] = time_bytes[0]
        payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1] = time_bytes[1]

        return payload

    def create_update_frame(self, current_humidity, current_temperature, door_status):
        """
        Create UPDATE_FRAME payload

        Args:
            current_humidity (int): Current humidity % (uint8)
            current_temperature (int): Current temperature in °C*10 (int16)
            door_status (int): Door status 0=closed, 1=open (uint8)

        Returns:
            bytearray: The frame payload
        """
        # Calculate total size
        total_size = UPDATE_FRAME_DOOR_STATUS_PLACE + 1
        payload = bytearray(total_size)

        # [0] Frame type identifier
        payload[0] = FrameType.UPDATE_FRAME

        # [1] Current humidity (uint8)
        payload[UPDATE_FRAME_CURRENT_HUMIDITY_PLACE] = current_humidity & 0xFF

        # [2-3] Current temperature (int16, 2 bytes, little-endian)
        temp_bytes = struct.pack('<h', current_temperature)
        payload[UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE] = temp_bytes[0]
        payload[UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE + 1] = temp_bytes[1]

        # [4] Door status (uint8)
        payload[UPDATE_FRAME_DOOR_STATUS_PLACE] = door_status & 0xFF

        return payload

    def publish_start_frame(self, command, meat_name, target_humidity, target_temperature,
                           current_humidity, current_temperature, door_status, time_of_smoking):
        """Publish START_FRAME to MQTT broker"""
        payload = self.create_start_frame(
            command, meat_name, target_humidity, target_temperature,
            current_humidity, current_temperature, door_status, time_of_smoking
        )

        print(f"\n📤 Publishing START_FRAME to '{MQTT_TOPIC_START}'")
        print(f"  Command: {command}")
        print(f"  Meat: {meat_name}")
        print(f"  Target - Temp: {target_temperature/10:.1f}°C, Humidity: {target_humidity}%")
        print(f"  Current - Temp: {current_temperature/10:.1f}°C, Humidity: {current_humidity}%")
        print(f"  Door: {'OPEN' if door_status else 'CLOSED'}")
        print(f"  Time: {time_of_smoking}s ({time_of_smoking//60}min)")
        print(f"  Payload size: {len(payload)} bytes")

        # Wyświetl ramkę w formacie binarnym (hex)
        self._print_frame_binary(payload, "START_FRAME")

        result = self.client.publish(MQTT_TOPIC_START, payload, qos=1)
        return result

    def publish_update_frame(self, current_humidity, current_temperature, door_status):
        """Publish UPDATE_FRAME to MQTT broker"""
        payload = self.create_update_frame(current_humidity, current_temperature, door_status)

        print(f"\n📤 Publishing UPDATE_FRAME to '{MQTT_TOPIC_UPDATE}'")
        print(f"  Current - Temp: {current_temperature/10:.1f}°C, Humidity: {current_humidity}%")
        print(f"  Door: {'OPEN' if door_status else 'CLOSED'}")
        print(f"  Payload size: {len(payload)} bytes")

        # Wyświetl ramkę w formacie binarnym (hex)
        self._print_frame_binary(payload, "UPDATE_FRAME")

        result = self.client.publish(MQTT_TOPIC_UPDATE, payload, qos=1)
        return result

    def _print_frame_binary(self, payload, frame_name):
        """Wyświetl ramkę w formacie binarnym/hex dla debugowania endianness"""
        print(f"\n  🔍 {frame_name} Binary Representation:")
        print(f"  {'Position':<10} {'Hex':<8} {'Dec':<6} {'Binary':<12} {'Description'}")
        print(f"  {'-'*70}")

        if frame_name == "START_FRAME":
            # [0] Frame Type
            print(f"  [0]        0x{payload[0]:02X}    {payload[0]:<6} {payload[0]:08b}    Frame Type (START_FRAME)")

            # [1] Command
            print(f"  [1]        0x{payload[1]:02X}    {payload[1]:<6} {payload[1]:08b}    Command")

            # [2-31] Meat name
            meat_str = payload[2:32].decode('utf-8', errors='ignore').rstrip('\x00')
            print(f"  [2-31]     {'...':<8} {'...':<6} {'...':<12}    Meat Name: '{meat_str}'")

            # [32] Target Humidity
            print(f"  [32]       0x{payload[32]:02X}    {payload[32]:<6} {payload[32]:08b}    Target Humidity")

            # [33-34] Target Temperature (int16, little-endian)
            temp_val = struct.unpack('<h', payload[33:35])[0]
            print(f"  [33]       0x{payload[33]:02X}    {payload[33]:<6} {payload[33]:08b}    Target Temp LOW byte")
            print(f"  [34]       0x{payload[34]:02X}    {payload[34]:<6} {payload[34]:08b}    Target Temp HIGH byte")
            print(f"  [33-34]    0x{payload[33]:02X}{payload[34]:02X}  {temp_val:<6} (little-endian) → {temp_val/10:.1f}°C")

            # [35] Current Humidity
            print(f"  [35]       0x{payload[35]:02X}    {payload[35]:<6} {payload[35]:08b}    Current Humidity")

            # [36-37] Current Temperature (int16, little-endian)
            curr_temp_val = struct.unpack('<h', payload[36:38])[0]
            print(f"  [36]       0x{payload[36]:02X}    {payload[36]:<6} {payload[36]:08b}    Current Temp LOW byte")
            print(f"  [37]       0x{payload[37]:02X}    {payload[37]:<6} {payload[37]:08b}    Current Temp HIGH byte")
            print(f"  [36-37]    0x{payload[36]:02X}{payload[37]:02X}  {curr_temp_val:<6} (little-endian) → {curr_temp_val/10:.1f}°C")

            # [38] Door Status
            print(f"  [38]       0x{payload[38]:02X}    {payload[38]:<6} {payload[38]:08b}    Door Status")

            # [39-40] Time of Smoking (uint16, little-endian)
            time_val = struct.unpack('<H', payload[39:41])[0]
            print(f"  [39]       0x{payload[39]:02X}    {payload[39]:<6} {payload[39]:08b}    Time LOW byte")
            print(f"  [40]       0x{payload[40]:02X}    {payload[40]:<6} {payload[40]:08b}    Time HIGH byte")
            print(f"  [39-40]    0x{payload[39]:02X}{payload[40]:02X}  {time_val:<6} (little-endian) → {time_val}s")

        elif frame_name == "UPDATE_FRAME":
            # [0] Frame Type
            print(f"  [0]        0x{payload[0]:02X}    {payload[0]:<6} {payload[0]:08b}    Frame Type (UPDATE_FRAME)")

            # [1] Current Humidity
            print(f"  [1]        0x{payload[1]:02X}    {payload[1]:<6} {payload[1]:08b}    Current Humidity")

            # [2-3] Current Temperature (int16, little-endian)
            temp_val = struct.unpack('<h', payload[2:4])[0]
            print(f"  [2]        0x{payload[2]:02X}    {payload[2]:<6} {payload[2]:08b}    Current Temp LOW byte")
            print(f"  [3]        0x{payload[3]:02X}    {payload[3]:<6} {payload[3]:08b}    Current Temp HIGH byte")
            print(f"  [2-3]      0x{payload[2]:02X}{payload[3]:02X}  {temp_val:<6} (little-endian) → {temp_val/10:.1f}°C")

            # [4] Door Status
            print(f"  [4]        0x{payload[4]:02X}    {payload[4]:<6} {payload[4]:08b}    Door Status")

        print(f"  {'-'*70}")

        # Wyświetl całą ramkę jako hex dump
        hex_str = ' '.join([f'{b:02X}' for b in payload])
        print(f"  Full frame (hex): {hex_str}")
        print()


def example_usage():
    """Example usage of the MQTT client"""

    # Create client instance
    client = MQTTSmokehouseClient()

    # Connect to broker
    if not client.connect():
        return

    try:
        # Example 1: Send START_FRAME to begin smoking process
        print("\n" + "="*60)
        print("Example 1: Starting smoking process for bacon")
        print("="*60)

        client.publish_start_frame(
            command=1,                    # Start command
            meat_name="Bacon",            # Meat type
            target_humidity=75,           # 75% humidity
            target_temperature=650,       # 65.0°C (stored as 65*10)
            current_humidity=45,          # Current 45%
            current_temperature=230,      # Current 23.0°C
            door_status=0,                # Door closed
            time_of_smoking=23          # 23 seconds
        )

        time.sleep(2)

        # Example 2: Send UPDATE_FRAME with current sensor readings
        print("\n" + "="*60)
        print("Example 2: Sending sensor update")
        print("="*60)

        client.publish_update_frame(
            current_humidity=68,          # Current 68%
            current_temperature=580,      # Current 58.0°C
            door_status=0                 # Door still closed
        )

        time.sleep(2)

        # Example 3: Another update
        print("\n" + "="*60)
        print("Example 3: Sending another update")
        print("="*60)

        client.publish_update_frame(
            current_humidity=72,          # Getting closer to target
            current_temperature=640,      # Almost at target
            door_status=0                 # Door still closed
        )

        time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        # Disconnect
        client.disconnect()


def simulate_smoking_process_reactive(duration_seconds=20, update_interval=2):
    """
    REACTIVE simulation - responds to ESP32 state changes
    Wysyła ramki UPDATE dopóki ESP32 nie zmieni stanu

    Args:
        duration_seconds (int): Total cooking time (używane w START_FRAME)
        update_interval (int): Seconds between UPDATE_FRAME messages
    """
    import random

    # Create client instance
    client = MQTTSmokehouseClient()

    # Connect to broker
    if not client.connect():
        return

    # Simulation parameters
    target_temp = 650        # 65.0°C
    target_humidity = 75     # 75%
    start_temp = 230         # 23.0°C (room temperature)
    start_humidity = 45      # 45% (room humidity)
    cooldown_temp = 400      # 40.0°C (cooldown target)

    current_temp = start_temp
    current_humidity = start_humidity
    update_count = 0
    confirmation_sent = False  # Flaga żeby wysłać potwierdzenie tylko raz

    try:
        # Send START_FRAME to begin smoking process
        print("\n" + "="*70)
        print("REACTIVE SIMULATION - Following ESP32 State Machine")
        print("="*70)
        print(f"Target: {target_temp/10:.1f}°C, {target_humidity}% humidity")
        print(f"Cooking duration: {duration_seconds}s")
        print("="*70)

        client.publish_start_frame(
            command=1,
            meat_name="Reactive Simulation",
            target_humidity=target_humidity,
            target_temperature=target_temp,
            current_humidity=int(current_humidity),
            current_temperature=int(current_temp),
            door_status=0,
            time_of_smoking=duration_seconds
        )

        time.sleep(2)

        print("\n🔄 Starting reactive loop - waiting for ESP32 state changes...\n")

        # Main reactive loop
        while True:
            current_state = client.last_state

            if current_state == "HEATING":
                # Zwiększaj temperaturę stopniowo
                if current_temp < target_temp:
                    current_temp += random.uniform(15, 30)  # Szybszy wzrost
                    current_temp = min(current_temp, target_temp + 20)  # Nie przekraczaj za bardzo
                else:
                    current_temp = target_temp + random.uniform(-10, 10)

                current_humidity = start_humidity + random.uniform(0, 5)

                update_count += 1
                print(f"[{current_state}] Update #{update_count} - Temp: {current_temp/10:.1f}°C → {target_temp/10:.1f}°C, Humidity: {int(current_humidity)}%")

            elif current_state == "HUMIDIFYING":
                # Utrzymuj temperaturę, zwiększaj wilgotność
                current_temp = target_temp + random.uniform(-15, 15)

                if current_humidity < target_humidity:
                    current_humidity += random.uniform(2, 5)
                    current_humidity = min(current_humidity, target_humidity + 5)
                else:
                    current_humidity = target_humidity + random.uniform(-3, 3)

                update_count += 1
                print(f"[{current_state}] Update #{update_count} - Temp: {current_temp/10:.1f}°C, Humidity: {int(current_humidity)}% → {target_humidity}%")

            elif current_state == "COOKING":
                # Utrzymuj temperaturę i wilgotność - wysyłaj aż ESP zmieni na FINISHED_COOKING
                current_temp = target_temp + random.uniform(-20, 20)
                current_humidity = target_humidity + random.uniform(-5, 5)

                update_count += 1
                print(f"[{current_state}] Update #{update_count} - Maintaining Temp: {current_temp/10:.1f}°C, Humidity: {int(current_humidity)}%")

            elif current_state == "FINISHED_COOKING":
                # Kontynuuj wysyłanie (ESP przejdzie do COOLDOWN)
                current_temp = target_temp + random.uniform(-20, 20)
                current_humidity = target_humidity + random.uniform(-5, 5)

                update_count += 1
                print(f"[{current_state}] Update #{update_count} - Temp: {current_temp/10:.1f}°C, Humidity: {int(current_humidity)}%")

            elif current_state == "COOLDOWN":
                # Zmniejszaj temperaturę aż ESP zmieni na READY_TO_TAKE_OUT
                if current_temp > cooldown_temp:
                    current_temp -= random.uniform(10, 20)
                    current_temp = max(current_temp, cooldown_temp - 20)
                else:
                    current_temp = cooldown_temp - random.uniform(0, 20)

                current_humidity -= random.uniform(1, 3)
                current_humidity = max(current_humidity, start_humidity)

                update_count += 1
                print(f"[{current_state}] Update #{update_count} - Cooling Temp: {current_temp/10:.1f}°C → 40°C, Humidity: {int(current_humidity)}%")

            elif current_state == "READY_TO_TAKE_OUT":
                # ESP wyświetla "READY TO TAKE OUT" - przejdzie do WAIT_FOR_TAKE_OUT_CONFIRMATION
                print(f"\n{'='*70}")
                print(f"[{current_state}] ESP32 ready - waiting for next state...")
                print(f"{'='*70}\n")
                time.sleep(update_interval)
                continue

            elif current_state == "WAIT_FOR_TAKE_OUT_CONFIRMATION":
                # ESP czeka na potwierdzenie - wyślij START_FRAME z command=0xAA (tylko raz)
                if not confirmation_sent:
                    print(f"\n{'='*70}")
                    print(f"[{current_state}] Sending CONFIRMATION (command=0xAA)")
                    print(f"{'='*70}\n")

                    client.publish_start_frame(
                        command=0xAA,  # Potwierdzenie
                        meat_name="Confirmation",
                        target_humidity=target_humidity,
                        target_temperature=target_temp,
                        current_humidity=int(current_humidity),
                        current_temperature=int(current_temp),
                        door_status=0,
                        time_of_smoking=0
                    )

                    confirmation_sent = True
                    print("✓ Confirmation sent, waiting for ESP32 to return to IDLE...\n")

                time.sleep(update_interval)
                continue

            elif current_state == "IDLE":
                if update_count > 0:
                    # Proces zakończony
                    print(f"\n{'='*70}")
                    print("✓ ESP32 returned to IDLE - Process Complete!")
                    print(f"{'='*70}")
                    break
                else:
                    # Czekamy na START
                    print(f"[{current_state}] Waiting for ESP32 to process START_FRAME...")
                    time.sleep(update_interval)
                    continue

            elif current_state == "UNKNOWN":
                # Czekamy na pierwszy stan
                print(f"[{current_state}] Waiting for ESP32 connection...")
                time.sleep(update_interval)
                continue

            else:
                print(f"[{current_state}] Unknown state, continuing...")

            # Wyślij UPDATE_FRAME tylko dla stanów które go wymagają
            if current_state in ["HEATING", "HUMIDIFYING", "COOKING", "FINISHED_COOKING", "COOLDOWN"]:
                client.publish_update_frame(
                    current_humidity=int(current_humidity),
                    current_temperature=int(current_temp),
                    door_status=0
                )

            time.sleep(update_interval)

        # Final summary
        print("\n" + "="*70)
        print("SIMULATION COMPLETE")
        print("="*70)
        print(f"Total updates sent: {update_count}")
        print(f"\nState transitions received from ESP32:")
        for i, state in enumerate(client.state_history, 1):
            print(f"  {i}. {state}")
        print(f"\nFinal temperature: {current_temp/10:.1f}°C")
        print(f"Final humidity: {int(current_humidity)}%")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
    finally:
        client.disconnect()


def simulate_smoking_process( duration_seconds=20, update_interval=2):
    """
    OLD VERSION - Time-based simulation (not reactive to ESP32 states)
    This simulates the full state machine cycle:
    IDLE -> HEATING -> HUMIDIFYING -> COOKING -> FINISHED -> COOLDOWN -> READY_TO_TAKE_OUT

    Args:
        duration_seconds (int): Total simulation duration in seconds (cooking time)
        update_interval (int): Seconds between UPDATE_FRAME messages
    """
    import random

    # Create client instance
    client = MQTTSmokehouseClient()

    # Connect to broker
    if not client.connect():
        return

    # Simulation parameters
    target_temp = 650        # 65.0°C
    target_humidity = 75     # 75%
    start_temp = 230         # 23.0°C (room temperature)
    start_humidity = 45      # 45% (room humidity)
    cooldown_temp = 400      # 40.0°C (cooldown target from your code)

    current_temp = start_temp
    current_humidity = start_humidity

    # Phases of the simulation
    # Phase 1: HEATING (0-25% of time) - reach target temp
    # Phase 2: HUMIDIFYING (25-40% of time) - reach target humidity
    # Phase 3: COOKING (40-100% of time) - maintain temp/humidity
    # Phase 4: COOLDOWN (after cooking) - cool down to 40°C
    # Phase 5: CONFIRMATION - send confirmation frame

    try:
        # Send START_FRAME to begin smoking process
        print("\n" + "="*70)
        print("SIMULATION START - Complete Smoking Cycle")
        print("="*70)
        print(f"Cooking duration: {duration_seconds} seconds")
        print(f"Update interval: {update_interval} seconds")
        print(f"Target: {target_temp/10:.1f}°C, {target_humidity}% humidity")
        print(f"Phases: HEATING -> HUMIDIFYING -> COOKING -> COOLDOWN -> CONFIRMATION")
        print("="*70)

        client.publish_start_frame(
            command=1,                    # Start command
            meat_name="Bacon Simulation", # Meat type
            target_humidity=target_humidity,  # uint8
            target_temperature=target_temp,   # int16
            current_humidity=int(current_humidity),  # uint8
            current_temperature=int(current_temp),   # int16
            door_status=0,                # Door closed (uint8)
            time_of_smoking=duration_seconds  # uint16
        )

        print("\n--- Phase 1: HEATING (door CLOSED) ---\n")
        time.sleep(1)

        # === PHASE 1: HEATING ===
        start_time = time.time()
        update_count = 0
        phase_1_duration = duration_seconds * 0.25

        while (time.time() - start_time) < phase_1_duration:
            elapsed = time.time() - start_time

            # Rapidly increase temperature
            temp_progress = elapsed / phase_1_duration
            current_temp = start_temp + (target_temp - start_temp) * temp_progress
            current_temp += random.uniform(-20, 20)  # Add noise
            current_temp = int(current_temp)  # Convert to int16

            # Humidity slowly increases from ambient
            current_humidity = int(start_humidity + random.uniform(0, 5))

            update_count += 1
            print(f"[HEATING {elapsed:.1f}s] Update #{update_count} - Temp: {current_temp/10:.1f}°C, Humidity: {current_humidity}%")

            client.publish_update_frame(
                current_humidity=current_humidity,
                current_temperature=current_temp,
                door_status=0
            )

            time.sleep(update_interval)

        # === PHASE 2: HUMIDIFYING ===
        print("\n--- Phase 2: HUMIDIFYING (door CLOSED) ---\n")
        phase_2_start = time.time()
        phase_2_duration = duration_seconds * 0.15

        while (time.time() - phase_2_start) < phase_2_duration:
            elapsed = time.time() - phase_2_start

            # Hold temperature at target with variations
            current_temp = int(target_temp + random.uniform(-15, 15))

            # Increase humidity to target
            humid_progress = elapsed / phase_2_duration
            current_humidity = start_humidity + (target_humidity - start_humidity) * humid_progress
            current_humidity = int(current_humidity + random.uniform(-3, 3))

            update_count += 1
            print(f"[HUMIDIFYING {elapsed:.1f}s] Update #{update_count} - Temp: {current_temp/10:.1f}°C, Humidity: {current_humidity}%")

            client.publish_update_frame(
                current_humidity=current_humidity,
                current_temperature=current_temp,
                door_status=0
            )

            time.sleep(update_interval)

        # === PHASE 3: COOKING ===
        print("\n--- Phase 3: COOKING (maintaining temp/humidity, door CLOSED) ---\n")
        phase_3_start = time.time()
        phase_3_duration = duration_seconds * 0.6  # Most of the time

        while (time.time() - phase_3_start) < phase_3_duration:
            elapsed = time.time() - phase_3_start

            # Maintain both at target with small variations
            current_temp = int(target_temp + random.uniform(-20, 20))
            current_humidity = int(target_humidity + random.uniform(-5, 5))

            update_count += 1
            cooking_elapsed = elapsed
            cooking_total = phase_3_duration
            print(f"[COOKING {cooking_elapsed:.1f}/{cooking_total:.1f}s] Update #{update_count} - Temp: {current_temp/10:.1f}°C, Humidity: {current_humidity}%")

            client.publish_update_frame(
                current_humidity=current_humidity,
                current_temperature=current_temp,
                door_status=0
            )

            time.sleep(update_interval)

        # === PHASE 4: COOLDOWN ===
        print("\n--- Phase 4: COOLDOWN (cooling to 40°C, door CLOSED) ---\n")
        phase_4_start = time.time()
        phase_4_duration = 8  # 8 seconds to cool down

        while (time.time() - phase_4_start) < phase_4_duration:
            elapsed = time.time() - phase_4_start

            # Temperature gradually decreases
            cool_progress = elapsed / phase_4_duration
            current_temp = target_temp - (target_temp - cooldown_temp) * cool_progress
            current_temp = int(current_temp + random.uniform(-10, 10))

            # Humidity decreases as well
            current_humidity = target_humidity - (target_humidity - start_humidity) * cool_progress * 0.5
            current_humidity = int(current_humidity + random.uniform(-3, 3))

            update_count += 1
            print(f"[COOLDOWN {elapsed:.1f}s] Update #{update_count} - Temp: {current_temp/10:.1f}°C, Humidity: {current_humidity}%")

            client.publish_update_frame(
                current_humidity=current_humidity,
                current_temperature=current_temp,
                door_status=0
            )

            time.sleep(update_interval)

        # Ensure final temp is below 40°C (value is in °C*10, so 40°C = 400)
        current_temp = 380  # 38.0°C (int16 format: 380 = 38.0°C)
        current_humidity = 55  # (uint8)

        print(f"\n[COOLDOWN COMPLETE] Final Update - Temp: {current_temp/10:.1f}°C, Humidity: {current_humidity}%")
        client.publish_update_frame(
            current_humidity=current_humidity,
            current_temperature=current_temp,
            door_status=0
        )
        update_count += 1
        time.sleep(2)

        # === PHASE 5: WAIT FOR CONFIRMATION ===
        print("\n--- Phase 5: READY_TO_TAKE_OUT - Waiting for user confirmation ---\n")
        print("In real scenario, user would confirm meat removal from app/button")
        print("Sending final UPDATE_FRAME to confirm ready state...")

        # Send a final UPDATE_FRAME to show system is ready
        client.publish_update_frame(
            current_humidity=current_humidity,
            current_temperature=current_temp,
            door_status=0  # Door still closed, waiting for user
        )

        time.sleep(2)

        # Final status
        print("\n" + "="*70)
        print("SIMULATION COMPLETE - Full Cycle Executed")
        print("="*70)
        print(f"Total updates sent: {update_count}")
        print(f"\nState transitions RECEIVED from ESP32:")
        for i, state in enumerate(client.state_history, 1):
            print(f"  {i}. {state}")
        print(f"\nFinal temperature: {current_temp/10:.1f}°C")
        print(f"Final humidity: {int(current_humidity)}%")
        print(f"Door status: CLOSED throughout entire process")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
    finally:
        # Disconnect
        client.disconnect()


if __name__ == "__main__":
    print("Smart Smokehouse MQTT Client - REACTIVE Simulation Mode")
    print("="*60)

    # Run REACTIVE simulation - responds to ESP32 state changes
    # Cooking duration is sent in START_FRAME (ESP32 uses it for timing)
    # Update interval is how often we send sensor updates
    simulate_smoking_process_reactive(duration_seconds=11, update_interval=2)

    # To run OLD time-based simulation instead:
    # simulate_smoking_process(duration_seconds=20, update_interval=2)

    # To run simple examples instead:
    # example_usage()
