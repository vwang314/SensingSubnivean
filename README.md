# Sensing the Subnivean
Georgia Tech Spring 2021 interdisciplinary senior design project. 

The goal of this project is to create sensor for the subnivean that scientists can leave out for extended periods of time. These sensors are designed to sense ambient temperature, ambient humidity, snow temperature, and snow depth. Ambient measurements are made 3 meters above ground. We chose to use the ESP32 microcontroller. This board will record the measurements and then upload them to AWS IoT core where it can be stored in a DynamoDB and accessible to scientists through a website. A mesh network is also implemented in case some nodes may lack good Wifi connection.
