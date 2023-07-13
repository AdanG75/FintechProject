#include <SoftwareSerial.h>
#include <FPM.h>

#define SEND_FINGERPRINT 'S'
#define WITHOUT_SERIAL 0
#define WITH_SERIAL 1



#if (defined(__AVR__) || defined(ESP8266)) && !defined(__AVR_ATmega2560__)
  // For UNO and others without hardware serial, we must use software serial...
  #define flag WITHOUT_SERIAL
  // pin #10 (Rx Arduino) -> (Tx Sensor - yellow)
  // pin #11 (Tx Arduino) -> (Rx Sensor - white)
  SoftwareSerial fserial(10, 11);

  // pin #12 (Rx Arduino) -> (Tx Bluetooth)
  // pin #13 (Tx Arduino) -> (Rx Bluetooth)
  SoftwareSerial myBluetooth(12, 13);

#else
  // On Leonardo/M0/etc, others with hardware serial, use hardware serial!
  #define flag WITH_SERIAL
  // Tx1 Arduino -> (Rx Sensor - white)
  // Rx1 Arduino -> (Tx Sensor - yellow)
  #define fserial Serial1

  // Tx2 Arduino -> (Rx Bluetooth)
  // Rx2 Arduino -> (Tx Bluetooth)
  #define myBluetooth Serial2
#endif

FPM finger(&fserial);
FPM_System_Params params;

char value = '1';

void setup() {
    //Serial.begin(57600);
    myBluetooth.begin(57600);

    while (!myBluetooth);  // For Yun/Leo/Micro/Zero/...
    delay(100);
    
    
    myBluetooth.println("SEND IMAGE TO PC test");
    fserial.begin(57600);

    if (finger.begin()) {
        finger.readParams(&params);
        myBluetooth.println("Found fingerprint sensor!");
        myBluetooth.print("Capacity: "); myBluetooth.println(params.capacity);
        myBluetooth.print("Packet length: "); myBluetooth.println(FPM::packet_lengths[params.packet_len]);
        myBluetooth.print("Send: "); myBluetooth.print(SEND_FINGERPRINT); myBluetooth.println(" to catch fingerprint");
    }
    else {
        myBluetooth.println("Did not find fingerprint sensor :(");
        while (1) yield();
    }
}

void loop() {
  // Uncomment for UNO and others without hardware serial
  // if (flag == WITHOUT_SERIAL) {
  //   myBluetooth.listen();
  // }
    
  if (myBluetooth.available()){
    value = myBluetooth.read();      
    if (value == SEND_FINGERPRINT) {
      
      // Uncomment for UNO and others without hardware serial
      // if (flag == WITHOUT_SERIAL) {
      //   fserial.listen();
      // }
      
      stream_image();

      // Uncomment for UNO and others without hardware serial
      // if (flag == WITHOUT_SERIAL) {
      //   myBluetooth.listen();
      // }
     }
   }
}

void stream_image(void) {
  
    if (!set_packet_len_128()) {
        myBluetooth.println("Could not set packet length");
        return;
    }

    delay(100);
    
    int16_t p = -1;
    myBluetooth.println("Waiting for a finger...");
    while (p != FPM_OK) {
        p = finger.getImage();
        switch (p) {
            case FPM_OK:
                myBluetooth.println("Image taken");
                break;
            case FPM_NOFINGER:
                break;
            case FPM_PACKETRECIEVEERR:
                myBluetooth.println("Communication error");
                break;
            case FPM_IMAGEFAIL:
                myBluetooth.println("Imaging error");
                break;
            default:
                myBluetooth.println("Unknown error");
                break;
        }
        yield();
    }

    p = finger.downImage();
    switch (p) {
        case FPM_OK:
            myBluetooth.println("Starting image stream...");
            break;
        case FPM_PACKETRECIEVEERR:
            myBluetooth.println("Communication error");
            return;
        case FPM_UPLOADFAIL:
            myBluetooth.println("Cannot transfer the image");
            return;
    }

    /* header to indicate start of image stream to PC */
    myBluetooth.write('\t');
    bool read_finished;
    int16_t count = 0;

    while (true) {
        bool ret = finger.readRaw(FPM_OUTPUT_TO_STREAM, &myBluetooth, &read_finished);
        if (ret) {
            count++;
            if (read_finished)
                break;
        }
        else {
            myBluetooth.print("\r\nError receiving packet ");
            myBluetooth.println(count);
            return;
        }
        yield();
    }

    myBluetooth.println();
    myBluetooth.print(count * FPM::packet_lengths[params.packet_len]); myBluetooth.println(" bytes read.");
    myBluetooth.println("Image stream complete.");
}

/* no need to call this for R308 */
bool set_packet_len_128(void) {
    uint8_t param = FPM_SETPARAM_PACKET_LEN;
    uint8_t value = FPM_PLEN_128;
    int16_t p = finger.setParam(param, value);
    switch (p) {
        case FPM_OK:
            myBluetooth.println("Packet length set to 128 bytes");
            break;
        case FPM_PACKETRECIEVEERR:
            myBluetooth.println("Comms error");
            break;
        case FPM_INVALIDREG:
            myBluetooth.println("Invalid settings!");
            break;
        default:
            myBluetooth.println("Unknown error");
    }

    return (p == FPM_OK);
}
