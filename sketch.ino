#include <Arduino_RouterBridge.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;
uint8_t frame[8][13] = {0};

unsigned long ledOffTime = 0;
bool solidOn = false;

// 接收 Linux 端傳來的 104 個字元 ('1' 亮, '0' 滅)，即時更新 8x13 LED 矩陣
void updateMatrix(String bits) {
  int idx = 0;
  for (int r = 0; r < 8; r++) {
    for (int c = 0; c < 13; c++) {
      if (idx < bits.length() && bits.charAt(idx) == '1') {
        frame[r][c] = 1;
      } else {
        frame[r][c] = 0;
      }
      idx++;
    }
  }
  matrix.renderBitmap(frame, 8, 13);
}

void onEatFood() {
  solidOn = false;
  digitalWrite(LED_BUILTIN, HIGH);
  ledOffTime = millis() + 150;
}

void onGameOver() {
  solidOn = true;
  ledOffTime = 0;
  digitalWrite(LED_BUILTIN, HIGH);
}

void onGameStart() {
  solidOn = false;
  ledOffTime = 0;
  digitalWrite(LED_BUILTIN, LOW);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  matrix.begin();

  Bridge.begin();
  Bridge.provide("updateMatrix", updateMatrix);
  Bridge.provide("onEatFood", onEatFood);
  Bridge.provide("onGameOver", onGameOver);
  Bridge.provide("onGameStart", onGameStart);
}

void loop() {
  if (!solidOn && ledOffTime > 0 && millis() >= ledOffTime) {
    digitalWrite(LED_BUILTIN, LOW);
    ledOffTime = 0;
  }
}
