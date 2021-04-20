# -*- coding: utf-8 -*-

import serial
import numpy as np

class Conect_Sensor(object):
    def __init__(self, serial_port = 'COM5', baud_rate = 57600, width = 256, height = 288):
        self._serial_port = serial_port
        self._baud_rate = baud_rate
        self._width = width
        self._height = height
        self._fingerprint_length = int(self._height * self._width)
        self._read_length_fingerprint = int(self._fingerprint_length /2)

        self._mask = 0b00001111

        self._data_fingerprint = []
        self._default_response = (False,)

    def catch_data_fingerprint(self):
        self._data_fingerprint = np.zeros(self._fingerprint_length, 'uint8')
        count = 0
        try:
            # open the port; timeout is 1 sec; also resets the arduino
            ser = serial.Serial(self._serial_port, self._baud_rate, timeout=1)
        except Exception as e:
            print('Invalid port settings:', e)
            print()
            return self._default_response
        while ser.isOpen():
            try:
                # assumes everything recved at first is printable ascii
                curr = ser.read().decode()
                # based on the image_to_pc sketch, \t indicates start of the stream
                if curr != '\t':
                    # print the debug messages from arduino running the image_to_pc sketch
                    print(curr, end='')
                    continue
                for i in range(self._read_length_fingerprint): # start reciving image
                    byte = ser.read()
                    # if we get nothing after the 1 sec timeout period
                    if not byte:
                        print("Timeout!")
                        ser.close()
                        return self._default_response
                    # make each nibble a high nibble
                    if count < self._fingerprint_length:
                        self._data_fingerprint[count] = ((byte[0] >> 4) * 17)
                        count += 1
                        self._data_fingerprint[count] = ((byte[0] & self._mask) *17)
                        count += 1
                    
                
                # read anything that's left and print
                left = ser.read(100)
                print(left.decode('ascii', errors='ignore'))
                ser.close()
                
                print()
                return self._data_fingerprint
            except Exception as e:
                print("Read failed: ", e)
                ser.close()
                return self._default_response
            except KeyboardInterrupt:
                print("Closing port.")
                ser.close()
                return self._default_response

