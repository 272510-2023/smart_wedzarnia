#include "mqtt_functions.hpp"
#include <PubSubClient.h>
#include <freertos/FreeRTOS.h>
#include "globals.hpp"

// ---- Ustawienia MQTT ----
const char* mqtt_server = "192.168.0.104";
//const char* mqtt_server = "192.168.0.157"; // IP twojego komputera z Mosquitto
const int mqtt_port = 1883;
const char* mqtt_topic_pub = "robot/speed";
const char* mqtt_topic_sub = "robot/frame/#";
const char* mqtt_topic_state = "robot/state"; // TOPIC DLA STANÓW

// ---- FUNKCJA: Wyświetlanie surowych bajtów ----
void printRawBytes(byte* payload, unsigned int length) {
    Serial.println("========== SUROWE BAJTY ==========");
    Serial.print("Długość: ");
    Serial.println(length);
    Serial.print("Hex: ");
    for (unsigned int i = 0; i < length; i++) {
        if (payload[i] < 0x10) Serial.print("0");
        Serial.print(payload[i], HEX);
        Serial.print(" ");
    }
    Serial.println();
    Serial.print("Dec: ");
    for (unsigned int i = 0; i < length; i++) {
        Serial.print(payload[i]);
        Serial.print(" ");
    }
    Serial.println();
    Serial.print("Bin: ");
    for (unsigned int i = 0; i < length; i++) {
        for (int bit = 7; bit >= 0; bit--) {
            Serial.print((payload[i] >> bit) & 1);
        }
        Serial.print(" ");
    }
    Serial.println();
    Serial.println("==================================");
}

// ---- FUNKCJA: Szczegółowa analiza START_FRAME ----
void printStartFrameAnalysis(byte* payload, unsigned int length) {
    Serial.println("\n╔════════════════════════════════════════════════════════╗");
    Serial.println("║         ANALIZA START_FRAME - BAJT PO BAJCIE          ║");
    Serial.println("╚════════════════════════════════════════════════════════╝");

    // Typ ramki
    Serial.print("Bajt [0] - Type_Frame: 0x");
    if (payload[0] < 0x10) Serial.print("0");
    Serial.print(payload[0], HEX);
    Serial.print(" = ");
    Serial.print(payload[0], BIN);
    Serial.print("b = ");
    Serial.println(payload[0]);

    // Command
    Serial.print("\nBajt [");
    Serial.print(START_FRAME_COMMAND_VALUE_PLACE);
    Serial.print("] - Command: 0x");
    if (payload[START_FRAME_COMMAND_VALUE_PLACE] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_COMMAND_VALUE_PLACE], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_COMMAND_VALUE_PLACE], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_COMMAND_VALUE_PLACE]);

    // Meat name
    Serial.print("\nBajty [");
    Serial.print(START_FRAME_MEAT_NAME_PLACE);
    Serial.print("-");
    Serial.print(START_FRAME_MEAT_NAME_PLACE + MEAT_NAME_LENGTH - 1);
    Serial.print("] - Meat Name (");
    Serial.print(MEAT_NAME_LENGTH);
    Serial.println(" bajtów):");
    Serial.print("  Hex: ");
    for (int i = 0; i < MEAT_NAME_LENGTH; i++) {
        if (payload[START_FRAME_MEAT_NAME_PLACE + i] < 0x10) Serial.print("0");
        Serial.print(payload[START_FRAME_MEAT_NAME_PLACE + i], HEX);
        Serial.print(" ");
    }
    Serial.print("\n  ASCII: \"");
    for (int i = 0; i < MEAT_NAME_LENGTH; i++) {
        char c = payload[START_FRAME_MEAT_NAME_PLACE + i];
        if (c >= 32 && c <= 126) Serial.print(c);
        else Serial.print(".");
    }
    Serial.println("\"");

    // Target humidity
    Serial.print("\nBajt [");
    Serial.print(START_FRAME_TARGET_HUMIDITY_PLACE);
    Serial.print("] - Target Humidity: 0x");
    if (payload[START_FRAME_TARGET_HUMIDITY_PLACE] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_TARGET_HUMIDITY_PLACE], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_TARGET_HUMIDITY_PLACE], BIN);
    Serial.print("b = ");
    Serial.print(payload[START_FRAME_TARGET_HUMIDITY_PLACE]);
    Serial.println("%");

    // Target temperature (16-bit)
    Serial.print("\nBajty [");
    Serial.print(START_FRAME_TARGET_TEMPERATURE_PLACE);
    Serial.print("-");
    Serial.print(START_FRAME_TARGET_TEMPERATURE_PLACE + 1);
    Serial.println("] - Target Temperature (16-bit):");
    Serial.print("  Bajt [");
    Serial.print(START_FRAME_TARGET_TEMPERATURE_PLACE);
    Serial.print("]: 0x");
    if (payload[START_FRAME_TARGET_TEMPERATURE_PLACE] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_TARGET_TEMPERATURE_PLACE], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_TARGET_TEMPERATURE_PLACE], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_TARGET_TEMPERATURE_PLACE]);

    Serial.print("  Bajt [");
    Serial.print(START_FRAME_TARGET_TEMPERATURE_PLACE + 1);
    Serial.print("]: 0x");
    if (payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1]);

    // Little-endian (młodszy bajt pierwszy) - UŻYWANE
    int16_t temp_little = payload[START_FRAME_TARGET_TEMPERATURE_PLACE] |
        (payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1] << 8);
    Serial.print("  → Little-endian (LSB first) ✓ UŻYWANE: ");
    Serial.print(temp_little);
    Serial.println("°C");

    // Big-endian (starszy bajt pierwszy) - dla porównania
    int16_t temp_big = (payload[START_FRAME_TARGET_TEMPERATURE_PLACE] << 8) |
        payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1];
    Serial.print("  → Big-endian (MSB first) [nieużywane]: ");
    Serial.print(temp_big);
    Serial.println("°C");

    // Current humidity
    Serial.print("\nBajt [");
    Serial.print(START_FRAME_CURRENT_HUMIDITY_PLACE);
    Serial.print("] - Current Humidity: 0x");
    if (payload[START_FRAME_CURRENT_HUMIDITY_PLACE] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_CURRENT_HUMIDITY_PLACE], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_CURRENT_HUMIDITY_PLACE], BIN);
    Serial.print("b = ");
    Serial.print(payload[START_FRAME_CURRENT_HUMIDITY_PLACE]);
    Serial.println("%");

    // Current temperature (16-bit)
    Serial.print("\nBajty [");
    Serial.print(START_FRAME_CURRENT_TEMPERATURE_PLACE);
    Serial.print("-");
    Serial.print(START_FRAME_CURRENT_TEMPERATURE_PLACE + 1);
    Serial.println("] - Current Temperature (16-bit):");
    Serial.print("  Bajt [");
    Serial.print(START_FRAME_CURRENT_TEMPERATURE_PLACE);
    Serial.print("]: 0x");
    if (payload[START_FRAME_CURRENT_TEMPERATURE_PLACE] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_CURRENT_TEMPERATURE_PLACE], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_CURRENT_TEMPERATURE_PLACE], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_CURRENT_TEMPERATURE_PLACE]);

    Serial.print("  Bajt [");
    Serial.print(START_FRAME_CURRENT_TEMPERATURE_PLACE + 1);
    Serial.print("]: 0x");
    if (payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1]);

    int16_t curr_temp_little = payload[START_FRAME_CURRENT_TEMPERATURE_PLACE] |
        (payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1] << 8);
    Serial.print("  → Little-endian (LSB first) ✓ UŻYWANE: ");
    Serial.print(curr_temp_little);
    Serial.println("°C");

    int16_t curr_temp_big = (payload[START_FRAME_CURRENT_TEMPERATURE_PLACE] << 8) |
        payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1];
    Serial.print("  → Big-endian (MSB first) [nieużywane]: ");
    Serial.print(curr_temp_big);
    Serial.println("°C");

    // Door status
    Serial.print("\nBajt [");
    Serial.print(START_FRAME_DOOR_STATUS_PLACE);
    Serial.print("] - Door Status: 0x");
    if (payload[START_FRAME_DOOR_STATUS_PLACE] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_DOOR_STATUS_PLACE], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_DOOR_STATUS_PLACE], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_DOOR_STATUS_PLACE]);

    // Time of smoking (16-bit)
    Serial.print("\nBajty [");
    Serial.print(START_FRAME_TIME_OF_SMOKING_PLACE);
    Serial.print("-");
    Serial.print(START_FRAME_TIME_OF_SMOKING_PLACE + 1);
    Serial.println("] - Time of Smoking (16-bit):");
    Serial.print("  Bajt [");
    Serial.print(START_FRAME_TIME_OF_SMOKING_PLACE);
    Serial.print("]: 0x");
    if (payload[START_FRAME_TIME_OF_SMOKING_PLACE] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_TIME_OF_SMOKING_PLACE], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_TIME_OF_SMOKING_PLACE], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_TIME_OF_SMOKING_PLACE]);

    Serial.print("  Bajt [");
    Serial.print(START_FRAME_TIME_OF_SMOKING_PLACE + 1);
    Serial.print("]: 0x");
    if (payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1] < 0x10) Serial.print("0");
    Serial.print(payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1], HEX);
    Serial.print(" = ");
    Serial.print(payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1], BIN);
    Serial.print("b = ");
    Serial.println(payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1]);

    uint16_t time_little = payload[START_FRAME_TIME_OF_SMOKING_PLACE] |
        (payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1] << 8);
    Serial.print("  → Little-endian (LSB first) ✓ UŻYWANE: ");
    Serial.print(time_little);
    Serial.println("s");

    uint16_t time_big = (payload[START_FRAME_TIME_OF_SMOKING_PLACE] << 8) |
        payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1];
    Serial.print("  → Big-endian (MSB first) [nieużywane]: ");
    Serial.print(time_big);
    Serial.println("s");

    Serial.println("\n════════════════════════════════════════════════════════\n");
}

// ---- FUNKCJA: Konwersja enum na string ----
const char* getStateName(state_machine state) {
    switch (state) {
    case SM_IDLE: return "IDLE";
    case SM_HEATING: return "HEATING";
    case SM_HUMIDIFYING: return "HUMIDIFYING";
    case SM_COOKING: return "COOKING";
    case SM_FINISHED_COOKING: return "FINISHED_COOKING";
    case SM_COOLDOWN: return "COOLDOWN";
    case SM_READY_TO_TAKE_OUT: return "READY_TO_TAKE_OUT";
    case SM_WAIT_FOR_TAKE_OUT_CONFIRMATION: return "WAIT_FOR_TAKE_OUT_CONFIRMATION";
    case SM_ERROR: return "ERROR";
    default: return "UNKNOWN";
    }
}

void printFrame(const struct process& frame) {
    Serial.print("Typ ramki: ");
    Serial.println(frame.Type_Frame == START_FRAME ? "START_FRAME" :
        frame.Type_Frame == UPDATE_FRAME ? "UPDATE_FRAME" : "UNKNOWN");

    Serial.print("Machine_State: ");
    Serial.println(frame.Machine_State == SM_IDLE ? "IDLE" : "WORKING");

    if (frame.Type_Frame == START_FRAME) {
        Serial.print("command: ");
        Serial.println(frame.Process_values.command);

        Serial.print("meat_name: ");
        for (int i = 0; i < MEAT_NAME_LENGTH; i++) {
            Serial.print((char)frame.Process_values.meat_name[i]);
        }
        Serial.println();

        Serial.print("target_humidity: ");
        Serial.println(frame.Process_values.target_humidity);

        Serial.print("target_temperature: ");
        Serial.println(frame.Process_values.target_temperature);

        Serial.print("time_of_smoking: ");
        Serial.println(frame.Process_values.time_of_smoking);
    }

    Serial.print("current_humidity: ");
    Serial.println(frame.Update_values.current_humidity);

    Serial.print("current_temperature: ");
    Serial.println(frame.Update_values.current_temperature);

    Serial.print("door_status: ");
    Serial.println(frame.Update_values.door_status);
    Serial.println("-----------------------------");
}


// ---- Callback po odebraniu wiadomości ----
void callback(char* topic, byte* payload, unsigned int length) {

    if (length == 0) {
        Serial.println("[MQTT] Empty frame received - ignoring.");
        return;
    }

    uint8_t frameType = payload[0];

    // typ ramki musi być jednym ze zdefiniowanych w enum type_of_frame
    if (frameType != START_FRAME && frameType != UPDATE_FRAME) {
        Serial.print("[MQTT] Invalid frame type received: ");
        Serial.println(frameType);
        return;
    }

    // spradzenie minimalnej długości ramki
    if (frameType == START_FRAME && length < START_FRAME_MIN_LENGTH) {
        Serial.print("[MQTT] START_FRAME too short. Length: ");
        Serial.println(length);
        return;
    }

    if (frameType == UPDATE_FRAME && length < UPDATE_MIN_FRAME_LENGTH) {
        Serial.print("[MQTT] UPDATE_FRAME too short. Length: ");
        Serial.println(length);
        return;
    }

    struct process frame;
    memset(&frame, 0, sizeof(frame)); // bardzo ważne!

    frame.Machine_State = SM_IDLE;

    switch (payload[0]) {

    case START_FRAME:
        // *** DEBUGOWANIE: Wyświetl surowe bajty i analizę ***
        //printRawBytes(payload, length);
        //printStartFrameAnalysis(payload, length);

        frame.Type_Frame = START_FRAME;

        frame.Process_values.command = payload[START_FRAME_COMMAND_VALUE_PLACE];

        for (int i = 0; i < MEAT_NAME_LENGTH; i++) {
            frame.Process_values.meat_name[i] = payload[START_FRAME_MEAT_NAME_PLACE + i];
        }

        frame.Process_values.target_humidity = payload[START_FRAME_TARGET_HUMIDITY_PLACE];

        // Little-endian (młodszy bajt pierwszy)
        frame.Process_values.target_temperature =
            payload[START_FRAME_TARGET_TEMPERATURE_PLACE] |
            (payload[START_FRAME_TARGET_TEMPERATURE_PLACE + 1] << 8);

        // Big-endian (młodszy bajt pierwszy)
        frame.Process_values.time_of_smoking =
            payload[START_FRAME_TIME_OF_SMOKING_PLACE] |
            (payload[START_FRAME_TIME_OF_SMOKING_PLACE + 1] << 8);

        frame.Update_values.current_humidity = payload[START_FRAME_CURRENT_HUMIDITY_PLACE];
        frame.Update_values.current_temperature =
            payload[START_FRAME_CURRENT_TEMPERATURE_PLACE] |
            (payload[START_FRAME_CURRENT_TEMPERATURE_PLACE + 1] << 8);

        frame.Update_values.door_status = payload[START_FRAME_DOOR_STATUS_PLACE];

        bool startFrameValid = true;

        // zakresy temperatury/wilgotności
        if (frame.Process_values.target_humidity > HUMID_MAX_ALLOWED) {
            Serial.println("[MQTT] START_FRAME: target_humidity out of range");
            startFrameValid = false;
        }

        if (frame.Process_values.target_temperature < TEMP_MIN_ALLOWED ||
            frame.Process_values.target_temperature > TEMP_MAX_ALLOWED) {
            Serial.println("[MQTT] START_FRAME: target_temperature out of range");
            startFrameValid = false;
        }

        if (frame.Update_values.current_humidity > HUMID_MAX_ALLOWED) {
            Serial.println("[MQTT] START_FRAME: current_humidity out of range");
            startFrameValid = false;
        }

        if (frame.Update_values.current_temperature < TEMP_MIN_ALLOWED ||
            frame.Update_values.current_temperature > TEMP_MAX_ALLOWED) {
            Serial.println("[MQTT] START_FRAME: current_temperature out of range");
            startFrameValid = false;
        }

        // status drzwi
        if (frame.Update_values.door_status != DOOR_CLOSED_VALUE &&
            frame.Update_values.door_status != DOOR_OPEN_VALUE) {
            Serial.println("[MQTT] START_FRAME: door_status invalid value");
            startFrameValid = false;
        }

        // czas wędzenia
        if (frame.Process_values.time_of_smoking == 0 ||
            frame.Process_values.time_of_smoking > 24 * 60 * 60) {
            Serial.println("[MQTT] START_FRAME: time_of_smoking out of range");
            startFrameValid = false;
        }

        // wysyłanie ramki do kolejki, jeśli całość jest poprawna
        if (!startFrameValid) {
            Serial.println("[MQTT] START_FRAME validation failed - frame ignored.");
            break;
        }

        xQueueSendFromISR(myQueue, &frame, NULL);
        printFrame(frame);
        break;

    case UPDATE_FRAME:
        frame.Type_Frame = UPDATE_FRAME;

        frame.Update_values.current_humidity = payload[UPDATE_FRAME_CURRENT_HUMIDITY_PLACE];
        frame.Update_values.current_temperature =
            payload[UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE] |
            (payload[UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE + 1] << 8);

        frame.Update_values.door_status = payload[UPDATE_FRAME_DOOR_STATUS_PLACE];

        bool updateFrameValid = true;

        if (frame.Update_values.current_humidity > HUMID_MAX_ALLOWED) {
            Serial.println("[MQTT] UPDATE_FRAME: current_humidity out of range");
            updateFrameValid = false;
        }

        if (frame.Update_values.current_temperature < TEMP_MIN_ALLOWED ||
            frame.Update_values.current_temperature > TEMP_MAX_ALLOWED) {
            Serial.println("[MQTT] UPDATE_FRAME: current_temperature out of range");
            updateFrameValid = false;
        }

        if (frame.Update_values.door_status != DOOR_CLOSED_VALUE &&
            frame.Update_values.door_status != DOOR_OPEN_VALUE) {
            Serial.println("[MQTT] UPDATE_FRAME: door_status invalid value");
            updateFrameValid = false;
        }

        if (!updateFrameValid) {
            Serial.println("[MQTT] UPDATE_FRAME validation failed - frame ignored.");
            break;
        }

        xQueueSendFromISR(myQueue, &frame, NULL);
        printFrame(frame);
        break;

    default:
        Serial.println("Nieznany typ ramki MQTT!");
        break;
    }

}


// ---- Ponowne łączenie z brokerem ----
void reconnect() {
    while (!client.connected()) {
        Serial.print("Łączenie z MQTT...");
        if (client.connect("ESP32Client")) {
            Serial.println("połączono!");
            client.subscribe(mqtt_topic_sub);
        }
        else {
            Serial.print("Błąd, rc=");
            Serial.print(client.state());
            Serial.println(" ponawianie za 5s...");
            delay(5000);
        }
    }
}


void TaskMQTT(void* parameter) {
    state_machine received_state;

    while (1) {
        if (!client.connected()) reconnect();
        client.loop();  // <- tu musi być

        // *** NASŁUCHIWANIE KOLEJKI STANÓW ***
        if (xQueueReceive(stateQueue, &received_state, 0) == pdTRUE) {
            const char* stateName = getStateName(received_state);

            if (client.connected()) {
                bool result = client.publish(mqtt_topic_state, stateName);

                if (result) {
                    Serial.print("[TaskMQTT] Wysłano stan: ");
                    Serial.println(stateName);
                }
                else {
                    Serial.println("[TaskMQTT] BŁĄD wysyłania stanu!");
                }
            }
            else {
                Serial.println("[TaskMQTT] Brak połączenia - nie można wysłać stanu!");
            }
        }

        vTaskDelay(100 / portTICK_PERIOD_MS);
    }
}
