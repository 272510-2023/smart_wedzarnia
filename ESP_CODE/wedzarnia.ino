#include <WiFi.h>
#include <PubSubClient.h>
#include "globals.hpp"
#include "wifi_functions.hpp"
#include "mqtt_functions.hpp"
#include "simulation.hpp"
#include "pin_inicjalization.hpp"
// najpierw tworzysz obiekt WiFiClient
WiFiClient espClient;

// teraz możesz użyć go w PubSubClient
PubSubClient client(espClient);

unsigned long lastMsg = 0;
float speed = 0.0;



void setup() {
  
  Serial.begin(115200);
  Serial.println("Start programu");

  myQueue = xQueueCreate(1, sizeof(struct process));
  cmdQueue = xQueueCreate(1, sizeof(struct control_command));
  stateQueue = xQueueCreate(10,sizeof(state_machine));

  sem_temp_ready  = xSemaphoreCreateBinary();
  sem_humid_ready = xSemaphoreCreateBinary();
 
  setup_pins();

  setup_wifi();                  // połączenie WiFi
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  xTaskCreate(TaskMQTT, "MQTT", 4096 , NULL, 2, NULL);
  xTaskCreate(TaskTempHumid, "TempHumid", 4096, NULL, 1, NULL);
  xTaskCreate(TaskSimulation, "Simulation", 4096, NULL, 1, NULL);
  
}

void loop() {
  // pusta, bo wszystko robimy w taskach
}
