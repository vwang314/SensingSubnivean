#include "secrets.h"
#include <WiFiClientSecure.h>
#include <MQTTClient.h>
#include <ArduinoJson.h>
#include "WiFi.h"
#include <WiFiUdp.h>
#include <NTPClient.h>

// The MQTT topics that this device should publish/subscribe
#define AWS_IOT_PUBLISH_TOPIC   "esp32/pub"
#define AWS_IOT_SUBSCRIBE_TOPIC "esp32/sub"

WiFiClientSecure net = WiFiClientSecure();
MQTTClient client = MQTTClient(256);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP);


#include <DHT.h>
#define DHTPIN 4     // what pin we're connected to
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

#define RXD2 17   // <-- define your favourite RX pin
#define TXD2 16   // <-- define your favourite TX pin
unsigned char data[4]={};
float distance = 0.0;
float snowDepth = 0.0;

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
  while (!Serial);

  connectAWS();
  timeClient.begin();
  dht.begin();
  snowTempSens.begin();
  xTaskCreate(measure_distance, "ultrasonic", 10000, NULL,1,NULL);
}

void loop() {
  timeClient.update();
  hum = dht.readHumidity();
  temp = 1.0858*dht.readTemperature() - 6.6451;  //values to calibrate sensor
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

  
  //Send MQTT
  StaticJsonDocument<200> doc;
  doc["stationID"] = "st1";
  doc["timestamp"] = timeClient.getEpochTime();
  doc["ambTemp"] = temp;
  doc["ambHum"] = hum;
  doc["snowTemp"] = snowTemp;
  doc["snowDepth"] = snowDepth;
  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer); // print to client
  client.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer);
  delay(1000);
}

//Thread for ultrasonic sensor since timing is important
void measure_distance(void * parameter){
  for(;;){
    do {
      for(int i = 0; i < 4; i++){
        data[i] = Serial2.read();
      }
    } while (Serial2.read() == 0xff);
    Serial2.flush();
    if(data[0] == 0xff){
      int sum;
      sum = (data[0] + data[1] + data[2]) & 0x00FF;
      if(sum == data[3]){
        distance = (data[1] << 8) + data[2];
      } else {
        Serial.println("Checksum error");
      }
    } else {
      Serial.println("Error");
    }
    delay(100);  //!!!! Timing must be ~100 ms !!!! (idk why)
    snowDepth = 300 - distance;
    Serial.print("Snow depth: ");
    Serial.println(snowDepth);
  }
  vTaskDelete(NULL);
}

void connectAWS()
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.println("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  // Configure WiFiClientSecure to use the AWS IoT device credentials
  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);
  // Connect to the MQTT broker on the AWS endpoint we defined earlier
  client.begin(AWS_IOT_ENDPOINT, 8883, net);
  // Create a message handler
  client.onMessage(messageHandler);
  Serial.print("Connecting to AWS IOT");
  while (!client.connect(THINGNAME)) {
    Serial.print(".");
    delay(100);
  }
  if(!client.connected()){
    Serial.println("AWS IoT Timeout!");
    return;
  }
  // Subscribe to a topic
  client.subscribe(AWS_IOT_SUBSCRIBE_TOPIC);
  Serial.println("AWS IoT Connected!");
}

void messageHandler(String &topic, String &payload) {
  Serial.println("incoming: " + topic + " - " + payload);
}
