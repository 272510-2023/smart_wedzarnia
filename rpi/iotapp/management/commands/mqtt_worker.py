import ssl
import json
import os
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.utils import timezone
# Import Twoich modeli - zmień 'twoja_aplikacja' na nazwę swojej apki w Django
from sensors.models import SensorReading, DoorStatus 

class Command(BaseCommand):
    help = 'Uruchamia nasłuchiwanie MQTT dla czujników IoT'

    def handle(self, *args, **options):
        # Konfiguracja stałych (możesz to przenieść do settings.py w przyszłości)
        IOT_ENDPOINT = "apc4udnp426oi-ats.iot.eu-central-1.amazonaws.com"
        PORT = 8883
        TOPIC = "decoded/#"
        CLIENT_ID = "django-worker-subscriber"

        # Ścieżki do certyfikatów
        CERT_ROOT = os.path.expanduser("~/iot/certs/AmazonRootCA1.pem")
        CERT_FILE = os.path.expanduser("~/iot/certs/f397c6ef30d1506986fcfb78b23d519599e830bf5e15f66132f5f5cb678cd99c-certificate.pem.crt")
        KEY_FILE  = os.path.expanduser("~/iot/certs/f397c6ef30d1506986fcfb78b23d519599e830bf5e15f66132f5f5cb678cd99c-private.pem.key")

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS(f"Połączono z AWS IoT. Subskrypcja: {TOPIC}"))
                client.subscribe(TOPIC)
            else:
                self.stdout.write(self.style.ERROR(f"Błąd połączenia, kod: {rc}"))

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                topic = msg.topic
                
                # --- LOGIKA ROZPOZNAWANIA DANYCH ---
                
                # Przypadek 1: Dane środowiskowe (szukamy klucza 'temperature')
                if 'temperature' in payload:
                    SensorReading.objects.create(
                        marker=payload.get('marker', 1), # Domyślnie 1 jeśli brak w JSON
                        temperature=payload.get('temperature', 0.0),
                        humidity=payload.get('humidity', 0.0),
                        pressure=payload.get('pressure', 0.0),
                        gas_resistance=payload.get('gas_resistance_ohm', 0.0) # Mapowanie klucza
                    )
                    print(f"[{topic}] Zapisano odczyt temperatury.")

                # Przypadek 2: Dane drzwi (szukamy klucza 'open_status' lub 'alarm')
                elif 'open_status' in payload or 'alarm' in payload:
                    # Konwersja boolean jeśli przychodzi jako tekst/liczba
                    is_open = payload.get('open_status')
                    if isinstance(is_open, str):
                        is_open = is_open.lower() == 'true'
                    
                    DoorStatus.objects.create(
                        open_status=bool(is_open),
                        alarm=int(payload.get('alarm', 0))
                    )
                    print(f"[{topic}] Zapisano status drzwi.")
                
                else:
                    print(f"[{topic}] Nieznany format danych: {payload}")

            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR("Błąd dekodowania JSON"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Błąd zapisu do bazy: {e}"))

        # Inicjalizacja klienta MQTT
        client = mqtt.Client(client_id=CLIENT_ID)
        client.tls_set(ca_certs=CERT_ROOT,
                       certfile=CERT_FILE,
                       keyfile=KEY_FILE,
                       tls_version=ssl.PROTOCOL_TLSv1_2)
        
        client.on_connect = on_connect
        client.on_message = on_message

        self.stdout.write("Rozpoczynanie pętli MQTT...")
        client.connect(IOT_ENDPOINT, PORT, keepalive=60)
        
        # loop_forever blokuje ten proces, co jest pożądane dla workera
        client.loop_forever()
