/*
  Alexa 5-button wall box  —  NodeMCU ESP-12E (ESP8266, CP2102)

  Each button calls a Virtual Smart Home "URL Routine Trigger" URL.
  Each trigger shows up in the Alexa app as a doorbell-type device that you
  use as the "When this happens" part of an Alexa Routine:

    Button 1 (D5)  ->  Routine: turn plug ON
    Button 2 (D6)  ->  Routine: turn plug OFF
    Button 3 (D7)  ->  Routine: turn plug OFF, Wait 10 s, turn plug ON
    Button 4 (D1)  ->  Routine: turn lights ON
    Button 5 (D2)  ->  Routine: turn lights OFF

  Wiring (no resistors needed, internal pull-ups are used):
    one leg of each switch -> D5 / D6 / D7 / D1 / D2
    the diagonal leg of each switch -> any G (GND) pin
    (12x12 tact switches: legs on the same side are internally connected;
     use two legs that are diagonal from each other to be safe)

  Board setting in Arduino IDE: "NodeMCU 1.0 (ESP-12E Module)"
  (install the ESP8266 core via Boards Manager:
   http://arduino.esp8266.com/stable/package_esp8266com_index.json)
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecureBearSSL.h>

#define NUM_BTNS 5

// ---------- fill these in ----------
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// Paste the full trigger URLs from virtualsmarthome.xyz (URL Routine Trigger page)
const char* TRIGGER_URL[NUM_BTNS] = {
  "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=PASTE_ON_TRIGGER_HERE",
  "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=PASTE_OFF_TRIGGER_HERE",
  "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=PASTE_CYCLE_TRIGGER_HERE",
  "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=PASTE_LIGHTS_ON_TRIGGER_HERE",
  "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=PASTE_LIGHTS_OFF_TRIGGER_HERE"
};
// -----------------------------------

const uint8_t BTN_PIN[NUM_BTNS]  = { D5, D6, D7, D1, D2 };
const char*   BTN_NAME[NUM_BTNS] = { "PLUG ON", "PLUG OFF", "PLUG POWER CYCLE", "LIGHTS ON", "LIGHTS OFF" };
const uint8_t LED = LED_BUILTIN;          // blue LED on the ESP module, active LOW

const unsigned long DEBOUNCE_MS = 40;
const unsigned long LOCKOUT_MS  = 2000;   // ignore repeat presses for 2 s (stops double-triggers)

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

bool fireTrigger(int i) {
  connectWiFi();
  if (WiFi.status() != WL_CONNECTED) return false;

  std::unique_ptr<BearSSL::WiFiClientSecure> client(new BearSSL::WiFiClientSecure);
  client->setInsecure();            // skip certificate check (fine for a doorbell-style trigger)
  client->setBufferSizes(1024, 512);

  HTTPClient https;
  https.setTimeout(8000);
  https.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  if (!https.begin(*client, TRIGGER_URL[i])) {
    Serial.println("https.begin failed");
    return false;
  }
  int code = https.GET();
  Serial.printf("[%s] HTTP %d\n", BTN_NAME[i], code);
  https.end();
  return code >= 200 && code < 400;
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
        bool ok = fireTrigger(i);
        digitalWrite(LED, HIGH);
        if (ok) ledBlink(1, 150);   // one blink = sent
        else    ledBlink(5, 60);    // fast blinks = failed
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
