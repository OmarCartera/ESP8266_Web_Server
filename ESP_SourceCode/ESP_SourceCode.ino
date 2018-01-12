/******************************
 *     Author: Omar Gamal     *
 *   c.omargamal@gmail.com    *
 *                            *
 *     Hardware: ESP8266      *
 *       Language: C++        *
 *                            *
 *         25/8/2017          *
 *     ESP8266 Web Server     *
 ******************************/

// Serial.println sends a string followd by 2 '\n'

// wifi module library
#include "ESP8266WiFi.h"

// digital sensor pin
#define D8 15

// debugging led
#define LED 2

// just if you want to set your IPs
IPAddress staticIP(172,28,128,232);
IPAddress gateway(172,28,128,1);   //192.168.1.1
IPAddress subnet(255,255,255,0);


// initializing a web server
WiFiServer server(80);


// variables to hold command, wifi name and password
String sig;
String wifi;
String pass;

//special counter
char which = 0;

void setup()
{
  // digital sensor value
  pinMode(D8, INPUT);

  //notification led
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH);  //high = 0

  // setting baud rate to 115200
  Serial.begin(115200);

  // disconnect from wifi
  WiFi.disconnect();
  delay(2000);
}


void loop()
{
  // if there are incoming bytes --> enter the loop
  while(Serial.available())
  {
    //the received signal
    sig = Serial.readString();

    // search the available wifi
    if(sig == "scan")
    {
      // getting number of available networks
      int n = WiFi.scanNetworks();// WiFi.scanNetworks will return the number of networks found

      // looping them to get their names
      for (int i = 0; i < n; ++i)
      {
        // print SSID for each network found
        Serial.println(WiFi.SSID(i));
        delay(10);
      }
    }
    
    // connect to a wifi
    else if(sig == "connect")
    {
      if (which == 0)
      {
        while(!Serial.available());
        wifi = String(Serial.readString());
        which++;
      }

      if (which == 1)
      {
        while(!Serial.available());
        pass = String(Serial.readString());
        which = 0;

        // connecting
        WiFi.begin(wifi.c_str(), pass.c_str());

        delay(8000);

        // sending back the connection status to python
        if(WiFi.status() != WL_CONNECTED)
        {
          Serial.println("Failed!");
        }

        if(WiFi.status() == WL_CONNECTED)
        {          
          //if you want to set your IPs
          WiFi.config(staticIP, gateway, subnet);
          WiFi.hostname("ESP_Cartera");
          server.begin();
          
          Serial.println("Connected!");
        }
      }
    }

    // disconnect the wifi
    else if(sig == "disconnect")
    {
      WiFi.disconnect();
      delay(1500);
    }

    // start iploading data to the web server
    else if(sig == "start")
    {
      digitalWrite(LED, LOW);

      WiFiClient client;

      while(Serial.available() == 0)
      {        
        while ((!client) && (Serial.available() == 0))
        {
          client = server.available();
        }

        //Serial.println(client.readStringUntil('\r'));
        client.println("HTTP/1.1 200 OK");
        client.println("Content-Type: text/html");
        client.println("");
        client.println("<!DOCTYPE HTML>");
        client.println("<html>");
        client.println(analogRead(A0));
        client.println(digitalRead(D8));
        client.println("</html>");
        client.stop();
      }
    }

    // stop the web server
    else if(sig == "stop")
    {
      while(Serial.available() == 0)
      {
        digitalWrite(LED, HIGH);
      }
    }
  }
}
