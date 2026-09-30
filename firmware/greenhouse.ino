#include <WiFi.h>
#include <WebServer.h>
#include <PubSubClient.h>
#include <Preferences.h>
#include <DHT.h>
#include <algorithm>
#include "secrets.h"

constexpr uint8_t PIN_DHT = 4, PIN_SOIL = 34, PIN_PUMP = 26, PIN_LED = 2;
constexpr uint32_t PUMP_MAX_MS = 60'000;
constexpr uint32_t PUMP_PAUSE_MS = 15 * 60'000;

DHT dht(PIN_DHT, DHT22);
WebServer web(80);
WiFiClient net;
PubSubClient mqtt(net);
Preferences prefs;

struct Settings { uint8_t dryPct = 35, wetPct = 55; uint16_t rawDry = 3100, rawWet = 1250; } cfg;
struct State { float t = NAN, h = NAN; uint8_t soil = 0; bool pump = false; uint32_t pumpOn = 0, pumpOff = 0; } st;

uint8_t soilPercent(uint16_t raw) {
  long p = map(raw, cfg.rawDry, cfg.rawWet, 0, 100);
  return constrain(p, 0, 100);
}

uint16_t readSoilRaw() {
  uint16_t v[9];
  for (auto &x : v) { x = analogRead(PIN_SOIL); delay(3); }
  std::sort(v, v + 9);
  return v[4];
}

void setPump(bool on) {
  if (on == st.pump) return;
  st.pump = on;
  digitalWrite(PIN_PUMP, on);
  (on ? st.pumpOn : st.pumpOff) = millis();
  mqtt.publish("greenhouse/pump", on ? "ON" : "OFF", true);
}

void control() {
  const uint32_t now = millis();
  if (st.pump) {
    if (st.soil >= cfg.wetPct || now - st.pumpOn > PUMP_MAX_MS) setPump(false);
  } else if (st.soil <= cfg.dryPct && now - st.pumpOff > PUMP_PAUSE_MS) {
    setPump(true);
  }
}

void publish() {
  char buf[96];
  snprintf(buf, sizeof buf, "{\"t\":%.1f,\"h\":%.0f,\"soil\":%u,\"pump\":%s}", st.t, st.h, st.soil, st.pump ? "true" : "false");
  mqtt.publish("greenhouse/state", buf);
}

void handleRoot() {
  char page[700];
  snprintf(page, sizeof page,
    "<meta name=viewport content='width=device-width'><h2>Теплица</h2>"
    "<p>Воздух: %.1f °C, %.0f%%</p><p>Почва: %u%%</p><p>Насос: %s</p>"
    "<form action=/set>Порог полива <input name=dry value=%u>%% — до <input name=wet value=%u>%% "
    "<button>Сохранить</button></form>",
    st.t, st.h, st.soil, st.pump ? "работает" : "выключен", cfg.dryPct, cfg.wetPct);
  web.send(200, "text/html; charset=utf-8", page);
}

void handleSet() {
  uint8_t dry = web.arg("dry").toInt(), wet = web.arg("wet").toInt();
  if (dry >= 5 && wet <= 95 && wet > dry + 5) {
    cfg.dryPct = dry; cfg.wetPct = wet;
    prefs.putBytes("cfg", &cfg, sizeof cfg);
  }
  web.sendHeader("Location", "/"); web.send(303);
}

void setup() {
  pinMode(PIN_PUMP, OUTPUT); pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_PUMP, LOW);
  analogSetPinAttenuation(PIN_SOIL, ADC_11db);
  prefs.begin("gh");
  prefs.getBytes("cfg", &cfg, sizeof cfg);
  dht.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  mqtt.setServer(MQTT_HOST, 1883);
  web.on("/", handleRoot); web.on("/set", handleSet); web.begin();
}

void loop() {
  static uint32_t last = 0;
  web.handleClient();
  if (WiFi.status() == WL_CONNECTED && !mqtt.connected()) mqtt.connect("greenhouse");
  mqtt.loop();
  if (millis() - last < 2000) return;
  last = millis();
  st.t = dht.readTemperature(); st.h = dht.readHumidity();
  st.soil = soilPercent(readSoilRaw());
  control();
  publish();
  digitalWrite(PIN_LED, !digitalRead(PIN_LED));
}
