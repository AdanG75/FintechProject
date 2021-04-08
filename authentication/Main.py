from Conect_Sensor import Conect_Sensor
from Fingerprint import Fingerprint
import cv2 as cv

def get_raw_fingerprint(in_cloud = True, data_fingerprint = []):
    if in_cloud == False:
        conect_sensor = Conect_Sensor()
        data_fingerprint = conect_sensor.catch_data_fingerprint()

    if data_fingerprint[0] == False:
        return False
    
    fingerprint = Fingerprint()
    raw_image = fingerprint.reconstruction_fingerprint(data_fingerprint)
    cv.imwrite('raw.bmp', (raw_image))
    cv.imshow("raw_fingerprint", raw_image)
    cv.waitKey(0)
    cv.destroyAllWindows()
    

    return True




if __name__ == '__main__':
    get_raw_fingerprint(in_cloud=False)