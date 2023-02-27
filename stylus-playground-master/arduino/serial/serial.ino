
#include <Adafruit_LSM6DS3TRC.h>

// D2/SDA -> green
// D3/SCL -> white

Adafruit_LSM6DS3TRC lsm6ds3trc;

void setup() {

  Serial.begin(9600);
  while (!Serial);

  if (!lsm6ds3trc.begin_I2C()) {
    Serial.println("Failed to find LSM6DS3TR-C");
    while (true) {
      delay(100);
    }
  }

  //lsm6ds3trc.configInt1(false, false, true); // accelerometer DRDY on INT1
  //lsm6ds3trc.configInt2(false, true, false); // gyro DRDY on INT2
}

void loop() {

  sensors_event_t accel;
  sensors_event_t gyro;
  sensors_event_t temp;

  lsm6ds3trc.getEvent(&accel, &gyro, &temp);

  Serial.print(gyro.timestamp);
  Serial.print(",");

  Serial.print(accel.acceleration.x, 4);
  Serial.print(",");
  Serial.print(accel.acceleration.y, 4);
  Serial.print(",");
  Serial.print(accel.acceleration.z, 4);
  Serial.print(",");

  Serial.print(gyro.gyro.x, 4);
  Serial.print(",");
  Serial.print(gyro.gyro.y, 4);
  Serial.print(",");
  Serial.print(gyro.gyro.z, 4);
  Serial.print(",");

  Serial.println(temp.temperature);
  
  delay(5);
}
