#include <sys/_stdint.h>
#pragma once
#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
// ----------------- ENUM -----------------
enum state_machine {
    SM_IDLE,
    SM_HEATING,
    SM_HUMIDIFYING,
    SM_COOKING,
    SM_FINISHED_COOKING,
    SM_COOLDOWN,
    SM_READY_TO_TAKE_OUT,
    SM_WAIT_FOR_TAKE_OUT_CONFIRMATION,
    SM_ERROR
};

enum temp_state {
    TEMP_HEATING,
    TEMP_HOLDING,
    TEMP_COOLING
};

enum humid_state {
    HUMIDIFY_ON,
    HUMIDIFY_HOLD,
    HUMIDIFY_OFF
};

enum type_of_frame{
    NO_NEW_FRAME = 0,
    START_FRAME = 1,
    UPDATE_FRAME = 2
};

// ----------------- KONSTANSY -----------------


#define MEAT_NAME_LENGTH 30

#define START_FRAME_COMMAND_VALUE_PLACE 1
#define START_FRAME_MEAT_NAME_PLACE (START_FRAME_COMMAND_VALUE_PLACE + 1)
#define START_FRAME_TARGET_HUMIDITY_PLACE (START_FRAME_MEAT_NAME_PLACE + MEAT_NAME_LENGTH)
#define START_FRAME_TARGET_TEMPERATURE_PLACE (START_FRAME_TARGET_HUMIDITY_PLACE + 1)
#define START_FRAME_CURRENT_HUMIDITY_PLACE (START_FRAME_TARGET_TEMPERATURE_PLACE + 2)
#define START_FRAME_CURRENT_TEMPERATURE_PLACE (START_FRAME_CURRENT_HUMIDITY_PLACE + 1)
#define START_FRAME_DOOR_STATUS_PLACE (START_FRAME_CURRENT_TEMPERATURE_PLACE + 2)
#define START_FRAME_TIME_OF_SMOKING_PLACE (START_FRAME_DOOR_STATUS_PLACE + 1)

#define UPDATE_FRAME_CURRENT_HUMIDITY_PLACE 1
#define UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE (UPDATE_FRAME_CURRENT_HUMIDITY_PLACE + 1)
#define UPDATE_FRAME_DOOR_STATUS_PLACE (UPDATE_FRAME_CURRENT_TEMPERATURE_PLACE + 2)

// ----------------- STRUKTURY -----------------
struct update_value{
    int16_t current_temperature;
    uint8_t current_humidity;
    uint8_t door_status;
};

struct process_values{
    uint8_t command;
    char meat_name[MEAT_NAME_LENGTH];
    int16_t target_temperature;
    uint8_t target_humidity; 
    uint16_t time_of_smoking; // this time need to be received in secundes 

};

struct process{
    struct update_value Update_values;
    struct process_values Process_values;
    enum state_machine Machine_State;
    enum type_of_frame Type_Frame;
};

struct control_command {
    temp_state temp_cmd;
    humid_state humid_cmd;
    uint16_t target_temp;
    uint8_t target_humid;
};


// ----------------- QUEUE -----------------
inline QueueHandle_t myQueue;
inline QueueHandle_t cmdQueue;
inline QueueHandle_t stateQueue;  // KOLEJKA DO WYSYŁANIA STANÓW
// ------------------SEMAFORES--------------
inline SemaphoreHandle_t sem_temp_ready;
inline SemaphoreHandle_t sem_humid_ready;
