#include "freertos/projdefs.h"
#include "portmacro.h"
#include <sys/_stdint.h>
#include "Arduino.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "globals.hpp"
#include "pin_inicjalization.hpp"
#include "simulation.hpp"

// *** WSPÓŁDZIELONE ZMIENNE dla komunikacji między taskami ***
inline int16_t shared_current_temperature = 0;
inline uint8_t shared_current_humidity = 0;

void TaskTempHumid(void *param)
{
    int16_t actual_temperature = 0;
    uint8_t actual_humidity = 0;

    struct process frame;
    control_command cmd;

    // *** REGULATOR PI - parametry ***
    float integral = 0.0;
    float Kp = 2.5;              // Wzmocnienie proporcjonalne
    float Ki = 0.05;             // Wzmocnienie całkujące
    float integral_max = 100.0;  // Anti-windup
    uint32_t last_update = millis();

    while(1)
    {
        // --- 1. Pobieramy aktualizację temperatury/wilgotności ---
        if (xQueueReceive(myQueue, &frame, 0) == pdTRUE)
        {
            if (frame.Type_Frame == UPDATE_FRAME)
            {
                actual_temperature = frame.Update_values.current_temperature;
                actual_humidity    = frame.Update_values.current_humidity;
                
                // *** AKTUALIZUJ WSPÓŁDZIELONE ZMIENNE ***
                shared_current_temperature = actual_temperature;
                shared_current_humidity = actual_humidity;
            }
        }

        // --- 2. Pobieramy komendy sterujące z TaskSimulation ---
        xQueueReceive(cmdQueue, &cmd, 0);

        // --- 3. Sterowanie TEMPERATURĄ z regulatorem PI ---
        switch(cmd.temp_cmd)
        {
            case TEMP_HEATING:
            {
                int16_t error = cmd.target_temp - actual_temperature;
                
                if (actual_temperature < cmd.target_temp)
                {
                    // *** REGULATOR PI ***
                    uint32_t now = millis();
                    float dt = (now - last_update) / 1000.0;  // Czas w sekundach
                    last_update = now;
                    
                    // Człon proporcjonalny
                    float P = Kp * error;
                    
                    // Człon całkujący (z anti-windup)
                    integral += Ki * error * dt;
                    if (integral > integral_max) integral = integral_max;
                    if (integral < -integral_max) integral = -integral_max;
                    
                    // Wyjście regulatora
                    float output = P + integral;
                    
                    // Skalowanie do PWM (0-255)
                    int duty = (int)(output);
                    duty = constrain(duty, 80, 255);  // Minimum 80 dla stabilności
                    
                    ledcWrite(HEATING_PIN, duty);
                    
                    // Debug co ~1s
                    if (millis() % 1000 < 50) {
                        Serial.print("[PI] Error: ");
                        Serial.print(error);
                        Serial.print(", P: ");
                        Serial.print(P);
                        Serial.print(", I: ");
                        Serial.print(integral);
                        Serial.print(", PWM: ");
                        Serial.println(duty);
                    }
                }
                else
                {
                    // Temperatura osiągnięta
                    ledcWrite(HEATING_PIN, 0);
                    integral = 0;  // Reset całki
                    xSemaphoreGive(sem_temp_ready);
                }
            }
            break;


            case TEMP_HOLDING:
            {
                // *** REGULATOR PI dla utrzymania temperatury ***
                int16_t error = cmd.target_temp - actual_temperature;
                
                uint32_t now = millis();
                float dt = (now - last_update) / 1000.0;
                last_update = now;
                
                // Człon proporcjonalny (łagodniejszy niż przy nagrzewaniu)
                float P = 1.5 * error;
                
                // Człon całkujący
                integral += 0.03 * error * dt;
                if (integral > integral_max) integral = integral_max;
                if (integral < -integral_max) integral = -integral_max;
                
                // Wyjście
                float output = P + integral;
                int duty = (int)(output + 150);  // Offset 150 dla utrzymania
                duty = constrain(duty, 0, 255);
                
                ledcWrite(HEATING_PIN, duty);
            }
            break;


            case TEMP_COOLING:
                ledcWrite(HEATING_PIN, 0);
                integral = 0;  // Reset całki
                break;
        }


        // --- 4. Sterowanie WILGOTNOŚCIĄ ---
        switch(cmd.humid_cmd)
        {
            case HUMIDIFY_ON:
                if(actual_humidity < cmd.target_humid)
                    digitalWrite(WATER_PIN, HIGH);
                else {
                    digitalWrite(WATER_PIN, LOW);
                    xSemaphoreGive(sem_humid_ready);
                }
                break;

            case HUMIDIFY_HOLD:
                if(actual_humidity < cmd.target_humid)
                    digitalWrite(WATER_PIN, HIGH);
                else
                    digitalWrite(WATER_PIN, LOW);
                break;

            case HUMIDIFY_OFF:
                digitalWrite(WATER_PIN, LOW);
                break;
        }

        vTaskDelay(200 / portTICK_PERIOD_MS);
    }
}


void TaskSimulation(void *param)
{
    struct process frame;
    control_command cmd;

    // Inicjalny stan maszyny
    frame.Machine_State = SM_IDLE;

    uint32_t cooking_start_time = 0;  
    uint32_t cooking_duration_ms = 0;

    // tablica flag dla logowania stanów (zakładam max 10 stanów)
    bool state_logged[10] = {0};
    
    // *** TABLICA FLAG DLA WYSYŁANIA STANÓW PO MQTT (żeby wysłać tylko raz) ***
    bool state_sent[10] = {0};

    while(1)
    {
        // *** WYSYŁANIE AKTUALNEGO STANU DO KOLEJKI (tylko raz) ***
        if(!state_sent[frame.Machine_State])
        {
            state_machine current_state = frame.Machine_State;
            xQueueSend(stateQueue, &current_state, 0);
            state_sent[frame.Machine_State] = true;
            Serial.print("[TaskSimulation] Wysłano stan do MQTT: ");
            Serial.println(frame.Machine_State);
        }

        switch(frame.Machine_State)
        {
            case SM_IDLE:
                if(!state_logged[SM_IDLE])
                {
                    Serial.println("[TaskSimulation] Stan: IDLE");
                    state_logged[SM_IDLE] = true;
                }
                if (xQueueReceive(myQueue, &frame, portMAX_DELAY))
                {
                    if(frame.Type_Frame == START_FRAME)
                    {
                        Serial.println("[TaskSimulation] Odebrano START_FRAME, ustawiamy parametry procesu");
                        cmd.target_temp  = frame.Process_values.target_temperature;
                        cmd.target_humid = frame.Process_values.target_humidity;

                        cmd.temp_cmd  = TEMP_HEATING;
                        cmd.humid_cmd = HUMIDIFY_OFF;

                        xQueueSend(cmdQueue, &cmd, portMAX_DELAY);

                        frame.Machine_State = SM_HEATING;
                        state_logged[SM_HEATING] = false;
                        state_sent[SM_HEATING] = false;  // reset flagi wysyłania
                    }
                }
                break;

            case SM_HEATING:
                if(!state_logged[SM_HEATING])
                {
                    Serial.println("[TaskSimulation] Stan: HEATING");
                    state_logged[SM_HEATING] = true;
                }
                if(xSemaphoreTake(sem_temp_ready, portMAX_DELAY))
                {
                    Serial.println("[TaskSimulation] Temperatura osiągnięta, przechodzimy do HUMIDIFYING");
                    cmd.temp_cmd  = TEMP_HOLDING;
                    cmd.humid_cmd = HUMIDIFY_ON;
                    xQueueSend(cmdQueue, &cmd, portMAX_DELAY);

                    frame.Machine_State = SM_HUMIDIFYING;
                    state_logged[SM_HUMIDIFYING] = false;
                    state_sent[SM_HUMIDIFYING] = false;
                }
                break;

            case SM_HUMIDIFYING:
                if(!state_logged[SM_HUMIDIFYING])
                {
                    Serial.println("[TaskSimulation] Stan: HUMIDIFYING");
                    state_logged[SM_HUMIDIFYING] = true;
                }
                if(xSemaphoreTake(sem_humid_ready, portMAX_DELAY))
                {
                    Serial.println("[TaskSimulation] Wilgotność osiągnięta, zaczynamy COOKING");
                    cooking_start_time = millis();
                    cooking_duration_ms = (uint32_t)frame.Process_values.time_of_smoking * 1000;

                    cmd.temp_cmd  = TEMP_HOLDING;
                    cmd.humid_cmd = HUMIDIFY_HOLD;
                    xQueueSend(cmdQueue, &cmd, portMAX_DELAY);

                    frame.Machine_State = SM_COOKING;
                    state_logged[SM_COOKING] = false;
                    state_sent[SM_COOKING] = false;
                }
                break;

            case SM_COOKING:
                if(!state_logged[SM_COOKING])
                {
                    Serial.println("[TaskSimulation] Stan: COOKING");
                    state_logged[SM_COOKING] = true;
                }
                if (millis() - cooking_start_time >= cooking_duration_ms)
                {
                    Serial.println("[TaskSimulation] Czas wędzenia minął, przechodzimy do FINISHED_COOKING");
                    cmd.temp_cmd  = TEMP_COOLING;
                    cmd.humid_cmd = HUMIDIFY_OFF;
                    xQueueSend(cmdQueue, &cmd, portMAX_DELAY);

                    frame.Machine_State = SM_FINISHED_COOKING;
                    state_logged[SM_FINISHED_COOKING] = false;
                    state_sent[SM_FINISHED_COOKING] = false;
                }
                break;

            case SM_FINISHED_COOKING:
                if(!state_logged[SM_FINISHED_COOKING])
                {
                    Serial.println("[TaskSimulation] Stan: FINISHED_COOKING, przechodzimy do COOLDOWN");
                    state_logged[SM_FINISHED_COOKING] = true;
                }
                cmd.temp_cmd = TEMP_COOLING;
                cmd.humid_cmd = HUMIDIFY_OFF;
                xQueueSend(cmdQueue, &cmd, portMAX_DELAY);

                frame.Machine_State = SM_COOLDOWN;
                state_logged[SM_COOLDOWN] = false;
                state_sent[SM_COOLDOWN] = false;
                break;

            case SM_COOLDOWN:
                if(!state_logged[SM_COOLDOWN])
                {
                    Serial.println("[TaskSimulation] Stan: COOLDOWN - czekam na schłodzenie do 40°C (400)");
                    state_logged[SM_COOLDOWN] = true;
                }
                
                // *** UŻYJ WSPÓŁDZIELONEJ ZMIENNEJ zamiast xQueueReceive ***
                Serial.print("[COOLDOWN] Aktualna temperatura: ");
                Serial.print(shared_current_temperature);
                Serial.print(" (");
                Serial.print(shared_current_temperature / 10.0);
                Serial.println("°C)");
                
                // Sprawdź czy temperatura spadła poniżej 40°C (400 w formacie °C*10)
                if (shared_current_temperature <= 400)
                {
                    Serial.println("[TaskSimulation] Temperatura spadła poniżej 40°C, READY_TO_TAKE_OUT");
                    frame.Machine_State = SM_READY_TO_TAKE_OUT;
                    state_logged[SM_READY_TO_TAKE_OUT] = false;
                    state_sent[SM_READY_TO_TAKE_OUT] = false;
                }
                
                vTaskDelay(500 / portTICK_PERIOD_MS);  // Sprawdzaj co 500ms
                break;

            case SM_READY_TO_TAKE_OUT:
                if(!state_logged[SM_READY_TO_TAKE_OUT])
                {
                    Serial.println("[TaskSimulation] Stan: READY_TO_TAKE_OUT");
                    Serial.println("READY TO TAKE OUT!");
                    state_logged[SM_READY_TO_TAKE_OUT] = true;
                }
                frame.Machine_State = SM_WAIT_FOR_TAKE_OUT_CONFIRMATION;
                state_logged[SM_WAIT_FOR_TAKE_OUT_CONFIRMATION] = false;
                state_sent[SM_WAIT_FOR_TAKE_OUT_CONFIRMATION] = false;
                break;

            case SM_WAIT_FOR_TAKE_OUT_CONFIRMATION:
                if(!state_logged[SM_WAIT_FOR_TAKE_OUT_CONFIRMATION])
                {
                    Serial.println("[TaskSimulation] Stan: WAIT_FOR_TAKE_OUT_CONFIRMATION");
                    state_logged[SM_WAIT_FOR_TAKE_OUT_CONFIRMATION] = true;
                }
                if(xQueueReceive(myQueue, &frame, 0))
                {
                    if(frame.Process_values.command == 0xAA)
                    {
                        Serial.println("[TaskSimulation] Potwierdzenie odebrane, powrót do IDLE");
                        frame.Machine_State = SM_IDLE;
                        state_logged[SM_IDLE] = false;
                        state_sent[SM_IDLE] = false;
                    }
                }
                break;

            case SM_ERROR:
                if(!state_logged[SM_ERROR])
                {
                    Serial.println("[TaskSimulation] Stan: ERROR");
                    state_logged[SM_ERROR] = true;
                }
                vTaskDelay(1000 / portTICK_PERIOD_MS);
                break;
        }

        vTaskDelay(50 / portTICK_PERIOD_MS);
    }
}
