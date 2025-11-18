#include "esp32-hal-ledc.h"
#include "Arduino.h"
#include "pin_inicjalization.hpp"


void setup_pins(){
  ledcAttach(HEATING_PIN, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcAttach(FANS_PIN, PWM_FREQUENCY, PWM_RESOLUTION);
  pinMode(WATER_PIN,OUTPUT);
}
