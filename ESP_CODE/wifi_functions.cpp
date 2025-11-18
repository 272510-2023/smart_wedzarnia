#include "wifi_functions.hpp"
#include <WiFi.h>
#include "Arduino.h"


// const char* ssid = "UPCA7D5AB6";
// const char* password = "ty52vnptyuKx";

//Wifi from school 

const char* ssid = "IOT_wifi";
const char* password = "IOT_wifi2025";

// ---- Łączenie z WiFi ----
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Łączenie z ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Połączono z WiFi, IP: ");
  Serial.println(WiFi.localIP());
}
