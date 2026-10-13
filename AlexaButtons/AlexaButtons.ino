/*
  Alexa Button Box  —  NodeMCU ESP-12E (ESP8266, CP2102) on a GPIO 1-into-2 breakout

  Every button press is sent to the button server running on your home PC
  (server/alexa_button_server.py). The server then:
    - switches the Feit (Tuya) smart plug directly over your Wi-Fi, and
    - fires a virtualsmarthome.xyz trigger to run an Alexa routine for the lights.

    Button 1 (D5)  ->  /plug/on
    Button 2 (D6)  ->  /plug/off
    Button 3 (D7)  ->  /plug/cycle   (off, wait, on - the wait happens on the server)
    Button 4 (D1)  ->  /lights/on
    Button 5 (D2)  ->  /lights/off

  Wiring (no resistors needed, internal pull-ups are used):
    one leg of each switch -> S header of D5 / D6 / D7 / D1 / D2
    the diagonally opposite leg of each switch -> any G header (they can share one wire)

  Board setting in Arduino IDE: "NodeMCU 1.0 (ESP-12E Module)"
  (install the ESP8266 core via Boards Manager:
   http://arduino.esp8266.com/stable/package_esp8266com_index.json)
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

#define NUM_BTNS 5

// ---------- fill these in ----------
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// The PC running alexa_button_server.py (port must match "port" in its config.json)
const char* SERVER = "http://192.168.1.87:8765";
// Must match "token" in the server's config.json (stops other devices on your network pressing buttons)
const char* TOKEN  = "change-me";
// -----------------------------------

const char*   BTN_PATH[NUM_BTNS] = { "/plug/on", "/plug/off", "/plug/cycle", "/lights/on", "/lights/off" };
const uint8_t BTN_PIN[NUM_BTNS]  = { D5, D6, D7, D1, D2 };
const char*   BTN_NAME[NUM_BTNS] = { "PLUG ON", "PLUG OFF", "PLUG POWER CYCLE", "LIGHTS ON", "LIGHTS OFF" };
const uint8_t LED = LED_BUILTIN;          // blue LED on the ESP module, active LOW

const unsigned long DEBOUNCE_MS = 40;
const unsigned long LOCKOUT_MS  = 1000;   // ignore repeat presses for 1 s (stops double-triggers)

bool lastReading[NUM_BTNS] = { HIGH, HIGH, HIGH, HIGH, HIGH };
bool stableState[NUM_BTNS] = { HIGH, HIGH, HIGH, HIGH, HIGH };
unsigned long lastChange[NUM_BTNS] = { 0 };
unsigned long lastFire = 0;

void ledBlink(int times, int ms) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED, LOW);  delay(ms);
    digitalWrite(LED, HIGH); delay(ms);
  }
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Connecting to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    digitalWrite(LED, !digitalRead(LED));   // flicker while connecting
    delay(250);
    Serial.print(".");
  }
  digitalWrite(LED, HIGH);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nConnected, IP %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\nWiFi connect failed, will retry");
  }
}

bool sendCommand(int i) {
  connectWiFi();
  if (WiFi.status() != WL_CONNECTED) return false;

  String url = String(SERVER) + BTN_PATH[i] + "?token=" + TOKEN;
  WiFiClient client;
  HTTPClient http;
  http.setTimeout(6000);
  if (!http.begin(client, url)) {
    Serial.println("http.begin failed");
    return false;
  }
  int code = http.GET();
  Serial.printf("[%s] HTTP %d %s\n", BTN_NAME[i], code, code > 0 ? http.getString().c_str() : "");
  http.end();
  return code == 200;
}

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  digitalWrite(LED, HIGH);
  for (int i = 0; i < NUM_BTNS; i++) pinMode(BTN_PIN[i], INPUT_PULLUP);
  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);
  connectWiFi();
  ledBlink(2, 100);
}

void loop() {
  unsigned long now = millis();

  for (int i = 0; i < NUM_BTNS; i++) {
    bool reading = digitalRead(BTN_PIN[i]);
    if (reading != lastReading[i]) {
      lastChange[i] = now;
      lastReading[i] = reading;
    }
    if (now - lastChange[i] > DEBOUNCE_MS && reading != stableState[i]) {
      stableState[i] = reading;
      if (reading == LOW && now - lastFire > LOCKOUT_MS) {   // pressed
        lastFire = now;
        Serial.printf("Button %s pressed\n", BTN_NAME[i]);
        digitalWrite(LED, LOW);                              // LED on while sending
        bool ok = sendCommand(i);
        digitalWrite(LED, HIGH);
        if (ok) ledBlink(1, 150);   // one blink = done
        else    ledBlink(5, 60);    // fast blinks = failed (server off? plug unreachable?)
      }
    }
  }

  static unsigned long lastWifiCheck = 0;
  if (now - lastWifiCheck > 30000) {   // keep WiFi alive
    lastWifiCheck = now;
    connectWiFi();
  }
  delay(5);
}
