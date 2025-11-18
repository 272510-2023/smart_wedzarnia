#ifndef MQTT_FUNCTIONS_HPP
#define MQTT_FUNCTIONS_HPP

#include <PubSubClient.h>

extern PubSubClient client;
extern unsigned long lastMsg;
extern float speed;
extern const char* mqtt_server;
extern const int mqtt_port;

void callback(char* topic, byte* payload, unsigned int length);
void reconnect();
void TaskMQTT(void *parameter);

#endif
