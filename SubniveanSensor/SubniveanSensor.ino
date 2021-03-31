#include <ArduinoBearSSL.h>
#include <ArduinoECCX08.h>
#include <ArduinoMqttClient.h>
#include <WiFiNINA.h> // change to #include <WiFi101.h> for MKR1000
#include "arduino_secrets.h"
/////// Enter your sensitive data in arduino_secrets.h
const char ssid[]        = SECRET_SSID;
const char pass[]        = SECRET_PASS;
const char broker[]      = SECRET_BROKER;
const char* certificate  = SECRET_CERTIFICATE;
WiFiClient    wifiClient;            // Used for the TCP socket connection
BearSSLClient sslClient(wifiClient); // Used for SSL/TLS connection, integrates with ECC508
MqttClient    mqttClient(sslClient);


#include <DHT.h>
#define DHTPIN 7     // what pin we're connected to
#define DHTTYPE DHT22   // DHT 22  (AM2302)
DHT dht(DHTPIN, DHTTYPE); //// Initialize DHT sensor for normal 16mhz Arduino
float hum;  //Stores humidity value
float temp; //Stores temperature value


#include <OneWire.h>
#include <DallasTemperature.h>
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature snowTempSens(&oneWire);
float snowTemp;


#include <Arduino.h>
#include "wiring_private.h"
Uart ultrasonic(&sercom0, 5, 6, SERCOM_RX_PAD_1, UART_TX_PAD_0);
void SERCOM0_Handler(){
  ultrasonic.IrqHandler();
}
unsigned char data[4]={};
float distance;
float snowDepth;


void setup() {
  Serial.begin(115200);
  while (!Serial);
  if (!ECCX08.begin()) {
      Serial.println("No ECCX08 present!");
      while (1);
  }

  ArduinoBearSSL.onGetTime(getTime);
  sslClient.setEccSlot(0, certificate);

  // Optional, set the client id used for MQTT,
  // mqttClient.setId("clientId");
  mqttClient.onMessage(onMessageReceived);

  dht.begin();
  snowTempSens.begin();
  pinPeripheral(5, PIO_SERCOM_ALT);
  pinPeripheral(6, PIO_SERCOM_ALT);
  ultrasonic.begin(9600);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    // MQTT client is disconnected, connect
    connectMQTT();
  }

  // poll for new MQTT messages and send keep alives
  mqttClient.poll();

  hum = dht.readHumidity();
  temp= dht.readTemperature();
  //Print temp and humidity values to serial monitor
  Serial.print("Ambient Humidity: ");
  Serial.print(hum);
  Serial.print(" %, Ambient Temp: ");
  Serial.print(temp);
  Serial.println(" Celsius");
  snowTempSens.requestTemperatures();
  Serial.print("Snow temperature is: ");
  snowTemp = snowTempSens.getTempCByIndex(0);
  Serial.println(snowTemp);
  do{
    for(int i = 0; i < 4; i++){
      data[i] = ultrasonic.read();
    }
  } while(ultrasonic.read() == 0xff);
  ultrasonic.flush();
  if(data[0] == 0xff){
    int sum;
    sum = (data[0] + data[1] + data[2]) & 0x00FF;
    if(sum == data[3]){
      distance = (data[1]<<8) + data[2];
      if(distance > 30){
        Serial.print("Distance = ");
        Serial.print(distance);
        Serial.println("mm");
        snowDepth = 3 - (distance/1000);
        Serial.print("Snowdepth = ");
        Serial.print(snowDepth);
        Serial.println("m");
      } else {
        Serial.println("Distance below lower limit");
        snowDepth = -1;
      }
    } else {
      Serial.println("Error");
    }
  }
  
  mqttClient.beginMessage("arduino/outgoing");   //message topic
  mqttClient.print("{\"ambTemp\": ");
  mqttClient.print(temp);
  mqttClient.print(", \"ambHum\": ");
  mqttClient.print(hum);
  mqttClient.print(", \"snowTemp\": ");
  mqttClient.print(snowTemp);
  mqttClient.print(", \"snowDepth\": ");
  mqttClient.print(snowDepth);
  mqttClient.print("}");
  mqttClient.endMessage();
  delay(1000);
}


unsigned long getTime() {
  // get the current time from the WiFi module  
  return WiFi.getTime();
}

void connectWiFi() {
  Serial.print("Attempting to connect to SSID: ");
  Serial.print(ssid);
  Serial.print(" ");

  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    // failed, retry
    Serial.print(".");
    delay(5000);
  }
  Serial.println();

  Serial.println("You're connected to the network");
  Serial.println();
}

void connectMQTT() {
  Serial.print("Attempting to MQTT broker: ");
  Serial.print(broker);
  Serial.println(" ");

  while (!mqttClient.connect(broker, 8883)) {
    // failed, retry
    Serial.print(".");
    delay(5000);
  }
  Serial.println();

  Serial.println("You're connected to the MQTT broker");
  Serial.println();

  // subscribe to a topic
  mqttClient.subscribe("arduino/incoming");
}

void onMessageReceived(int messageSize) {
  // we received a message, print out the topic and contents
  Serial.print("Received a message with topic '");
  Serial.print(mqttClient.messageTopic());
  Serial.print("', length ");
  Serial.print(messageSize);
  Serial.println(" bytes:");

  // use the Stream interface to print the contents
  while (mqttClient.available()) {
    Serial.print((char)mqttClient.read());
  }
  Serial.println();

  Serial.println();
}
