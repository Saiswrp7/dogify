// Dog box: the laptop sends one letter over USB, the box acts and replies.
//   P -> OK   D -> distance in cm   T -> drop treat   B -> roll ball

const int TRIG = 4, ECHO = 5;
const int TREAT_SERVO = 6, BALL_SERVO = 7;

// SG90 servo: 50 Hz, pulse 0.5 ms (0 deg) to 2.5 ms (180 deg), 14-bit duty
void servoAngle(int pin, int angle) {
  int us = 500 + angle * 2000 / 180;
  ledcWrite(pin, (long)us * 16384 / 20000);
}

long distanceCm() {
  digitalWrite(TRIG, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long us = pulseIn(ECHO, HIGH, 30000);  // give up after 30 ms (~5 m)
  return us == 0 ? -1 : us / 58;
}

void move(int pin, int angle, int holdMs) {
  digitalWrite(LED_BUILTIN, HIGH);
  servoAngle(pin, angle);
  delay(holdMs);
  servoAngle(pin, 0);
  delay(300);
  digitalWrite(LED_BUILTIN, LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT_PULLDOWN);
  pinMode(LED_BUILTIN, OUTPUT);
  ledcAttach(TREAT_SERVO, 50, 14);
  ledcAttach(BALL_SERVO, 50, 14);
  servoAngle(TREAT_SERVO, 0);
  servoAngle(BALL_SERVO, 0);
}

void loop() {
  if (!Serial.available()) return;
  char c = toupper(Serial.read());
  if (c == 'P') Serial.println("OK");
  else if (c == 'D') { Serial.print("D "); Serial.println(distanceCm()); }
  else if (c == 'T') { move(TREAT_SERVO, 60, 400); Serial.println("T done"); }
  else if (c == 'B') { move(BALL_SERVO, 90, 1000); Serial.println("B done"); }
}
