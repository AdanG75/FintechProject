# -*- coding: utf-8 -*-
import functools
import json
from typing import Optional, Union, Any

import serial
import numpy as np


def connect_with_fingerprint_sensor(func):
    """
    A decorator to open connection with a fingerprint sensor.
    Only would be used by the class ConnectSensor.

    The class which implement the decorator must have the next params:
    - self: (ConnectSensor) The self ConnectSensor's instance which uses this instance
    - count: (int) The position of fingerprint data
    - byte: (Optional[bytes]) The data caught from fingerprint sensor
    """

    @functools.wraps(func)
    def wrapper(self, count: int, byte: Optional[bytes]):
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
                # assumes everything received at first is printable ascii
                curr = ser.read().decode()
                # based on the image_to_pc sketch, \t indicates start of the stream
                if curr != '\t':
                    # print the debug messages from arduino running the image_to_pc sketch
                    print(curr, end='')
                    continue

                for i in range(self._read_length_fingerprint):  # start receiving image
                    byte = ser.read()
                    # if we get nothing after the 1 sec timeout period
                    if not byte:
                        print("Timeout!")
                        ser.close()
                        return self._default_response

                    count = func(self, count, byte)

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

    return wrapper


class ConnectSensor(object):
    def __init__(self, serial_port='COM5', baud_rate=57600, width=256, height=288):
        super().__init__()
        self._serial_port = serial_port
        self._baud_rate = baud_rate
        self._width = width
        self._height = height
        self._fingerprint_length = int(self._height * self._width)
        self._read_length_fingerprint = int(self._fingerprint_length / 2)

        self._mask = 0b00001111

        self._data_fingerprint = []
        self._default_response = (False,)

    def catch_data_fingerprint(self):
        self.__convert_nibble_to_high_nibble(count=0, byte=bytes(0))

        if self._data_fingerprint == []:
            return self._default_response

        return self._data_fingerprint

    def save_fingerprint_into_json(
            self,
            path_json: str = './data/',
            name_json: str = 'fingerprintRawData'
    ) -> Union[tuple[bool], dict[str, list[Any]]]:

        self.__save_nibble(count=0, byte=bytes(0))

        all_int_raw_fingerprint_data = self._data_fingerprint.tolist()
        sensor_fingerprint_data = []

        for i in range(0, self._read_length_fingerprint):
            sensor_fingerprint_data.append(all_int_raw_fingerprint_data[i])

        fingerprint_dict = {
            "fingerprint": sensor_fingerprint_data
        }

        # json_object = json.dumps(fingerprint_dict, ensure_ascii=False, indent=4)
        try:
            with open(path_json + name_json + ".json", 'w', encoding='utf-8') as f:
                # f.write(json_object)
                json.dump(fingerprint_dict, f, ensure_ascii=False, indent=4)
                f.close()
        except Exception:
            return self._default_response

        return fingerprint_dict

    @connect_with_fingerprint_sensor
    def __convert_nibble_to_high_nibble(self, count: int = 0, byte: Optional[bytes] = bytes(0)):
        # make each nibble a high nibble
        if count < self._fingerprint_length:
            self._data_fingerprint[count] = ((byte[0] >> 4) * 17)
            count += 1
            self._data_fingerprint[count] = ((byte[0] & self._mask) * 17)
            count += 1

        return count

    @connect_with_fingerprint_sensor
    def __save_nibble(self, count: int = 0, byte: Optional[bytes] = bytes(0)):
        if count < self._fingerprint_length / 2:
            self._data_fingerprint[count] = byte[0]
            count += 1

        return count
