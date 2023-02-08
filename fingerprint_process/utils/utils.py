import base64
import io
import os.path
import random
import re
from typing import List, Union, Optional, Iterable

import cv2 as cv
from PIL import Image
from numpy import ndarray

from core.utils import save_object_as_json
from db.orm.exceptions_orm import compile_exception
from fingerprint_process.preprocessing.connect_sensor import ConnectSensor
from fingerprint_process.preprocessing.fingerprint_raw import FingerprintRaw
from fingerprint_process.description.fingerprint import Fingerprint
from fingerprint_process.preprocessing.quality_image import QualityFingerprint
from fingerprint_process.utils.bank_fingerprint_images import BankFingerprint
from fingerprint_process.matching.match import match
from fingerprint_process.utils.error_message import ErrorMessage
from schemas.fingerprint_model import FingerprintSamples


def create_fingerprint_samples():
    bank_fp = BankFingerprint(num_fingerprints=20, address_output='./authentication/sampleImages/',
                              name='Fingerprint_Test', extension='.bmp')
    bank_fp.generate_bank_fingerprint(auto_named=False)


def get_data_fingerprint(source: str = 'sensor', data_fingerprint: Union[str, list, None] = None):
    """
    A function to get the data of the raw fingerprint.

    :param source: A string which could be 'sensor' when the data is get from a serial port
                        and 'api' when is get from api.
    :param data_fingerprint: An int array or a string decoded in base64 which is obtained from api. Only it is used
                    when data come from api.

    :return: a tuple with this data (False,) when couldn't possible to get the raw fingerprint. On the other hand,
    return the raw fingerprint into a bit array.
    """
    if data_fingerprint is None:
        data_fingerprint = []

    if source.lower() == 'sensor':
        connect_sensor = ConnectSensor(serial_port='/dev/ttyUSB0', baud_rate=57600, width=256, height=288)
        data_fingerprint_raw = connect_sensor.catch_data_fingerprint()
    elif source.lower() == 'api':
        fingerprint_raw = FingerprintRaw()
        data_fingerprint_raw = fingerprint_raw.get_fingerprint_raw(data_fingerprint)
    else:
        return (False,)

    return data_fingerprint_raw


def change_directory_of_images():
    finish = False
    ubication_image = None

    while (not finish):
        ubication_image = './fingerprint_process/sampleImages/'
        print('\n\t Directory to search image: {}'.format(ubication_image))
        print('Would you like to change the directory by default:\n')
        print('\t [Y]es')
        print('\t [N]o')
        option = input('\nSelect you option: ')

        if (option[0].upper() == 'Y'):
            ubication_image = input('Write the new directory to search image: ')
            finish = True
        elif (option[0].upper() == 'N'):
            finish = True
        else:
            continue

    name_image = input('Write the image name (with extension): ')
    ubication_image += name_image

    return ubication_image


def get_description_fingerprint(
        name_fingerprint: str = 'fingerprint',
        source: str = 'sensor',
        data_fingerprint: Union[str, list] = '',
        address_image: str = '',
        mode: str = 'auth',
        show_result: bool = True,
        save_result: bool = True
) -> Union[Fingerprint, int, property]:
    """
    Obtain the full description of a fingerprint

    :param name_fingerprint: (str) The name that fingerprint object will receive
    :param source: (str) The place where will catch the fingerprint:
                    - 'sensor' when is caught from serial port
                    - 'image' when is caught from an image
                    - 'api' when is caught from the api
    :param data_fingerprint: (str, List[int]) Data of fingerprint which is represented as a string on base64 codec or as
                            a list of integers. Only is used when source is 'api'
    :param address_image: (str) The path where the image can be found. Only it is used
                            when the source is 'image'
    :param mode: (str) The reason the sample was captured. Could be 'register', 'auth' or 'match'
    :param show_result: (bool) True when we want to show all plots and sub-fingerprints
                        images generated by the application. Always False when source is 'api'.
    :param save_result: (bool) True when we want to save all plots and sub-fingerprints
                        images generated by the application. In case that source is 'api'
                        the application will only save the raw fingerprint.

    :return: a fingerprint object when all was ok, in other case return an ErrorMessage.

    """
    fingerprint = Fingerprint(
        characteritic_point_thresh=0.8,
        name_fingerprint=name_fingerprint,
        show_result=show_result,
        save_result=save_result
    )
    process_message = None

    if source.lower() == 'sensor':
        data_image = get_data_fingerprint(source='sensor')
        if len(data_image) < 2:
            print('Error to get the fingerprint image')
            process_message = ErrorMessage.VOID_FINGERPRINT
            return process_message

        process_message = fingerprint.describe_fingerprint(data_image, angles_tolerance=1, mode=mode)
    elif source.lower() == 'api':
        data_image = get_data_fingerprint(source='api', data_fingerprint=data_fingerprint)

        if len(data_image) < 2:
            print('Error to get the fingerprint image')
            process_message = ErrorMessage.VOID_FINGERPRINT
            return process_message

        process_message = fingerprint.describe_fingerprint(
            data_image,
            angles_tolerance=1,
            mode=mode,
            neighbors_description=False
        )
    elif source.lower() == 'image':
        if not address_image or address_image.isspace():
            address_image = change_directory_of_images()

        img = cv.imread(address_image, 0)
        # img = cv.imread('./authentication/sampleImages/Huella70.bmp', 0)

        if img is None:
            print('Error to get the fingerprint image')
            process_message = ErrorMessage.VOID_FINGERPRINT
            return process_message

        process_message = fingerprint.describe_fingerprint(
            angles_tolerance=1,
            from_image=True,
            fingerprint_image=img,
            mode=mode
        )

    else:
        return ErrorMessage.NOT_OPTION_FOUND

    if process_message == fingerprint.FINGERPRINT_OK:
        return fingerprint
    else:
        fingerprint.show_message(process_message)
        return process_message


def capture_good_quality_fingerprints() -> bool:
    NO_ERROR_VALUE = 0
    name_pattern: str = r"^\w{3,20}$"
    name_fingerprint = input("Write the name of the fingerprint sample: ")
    if re.match(name_pattern, name_fingerprint) is None:
        print("Name no valid")
        return False

    int_pattern = r"^[1-9]\d{0,2}$"
    times = input("Indicate the number of fingerprint samples to be captured: ")
    if re.match(int_pattern, times) is not None:
        times_int = int(times)
    else:
        print("Type of value no valid")
        return False

    lines = ["SAMPLE NAME,REGISTER VALUE,AUTH VALUE,SPATIAL VALUE\n"]

    fingerprint = Fingerprint(
        name_fingerprint=name_fingerprint,
        show_result=False,
        save_result=True
    )

    base_path = f"./fingerprint_process/preprocessing_fingerprints/best_fingerprints/{name_fingerprint}/"
    if not os.path.isdir(base_path):
        os.makedirs(base_path)

    file_name = f"{name_fingerprint}_data.csv"

    time = 0
    while time < times_int:
        data_fingerprint = get_data_fingerprint()
        if isinstance(data_fingerprint, tuple):
            pass

        (result, reg_quality, auth_quality, spatial_quality) = fingerprint.get_good_quality_fingerprint(
            data_fingerprint=data_fingerprint,
            time=time,
            name_sample=name_fingerprint,
            base_path=base_path
        )

        text = f"Sample_{time},{reg_quality},{auth_quality},{spatial_quality}\n"
        if result == NO_ERROR_VALUE:
            print("Good quality fingerprint sample detected")
            print(text)

            lines.append(text)
            time += 1
        else:
            print("Bad quality fingerprint :(")
            print(text)

    with open(base_path+file_name, "w+", encoding='utf-8') as f:
        for line in lines:
            f.write(line)

    return True


def match_index_and_base_fingerprints(
        base_name: str,
        input_name: str,
        mode: str,
        source: str,
        base_fingerprint: Optional[Fingerprint] = None,
        input_fingerprint: Optional[Fingerprint] = None
):

    if source.lower() == 'sensor':
        base_fingerprint = get_description_fingerprint(name_fingerprint=base_name, source=source.lower())
        input_fingerprint = get_description_fingerprint(name_fingerprint=input_name, source=source.lower())
    elif source.lower() == 'image':
        base_fingerprint = get_description_fingerprint(name_fingerprint=base_name, source=source.lower())
        input_fingerprint = get_description_fingerprint(name_fingerprint=input_name, source=source.lower())
    elif source.lower() == 'api':
        if base_fingerprint is None or input_fingerprint is None:
            return ErrorMessage.VOID_FINGERPRINT
    else:
        return ErrorMessage.NOT_OPTION_FOUND

    return match(base_fingerprint, input_fingerprint, mode)


def save_fingerprint_into_json(
        serial_port: str = '/dev/ttyUSB0',
        baud_rate: int = 57600,
        path_json: str = "./fingerprint_process/data/",
        name_json: str = "fingerprintRawData"
):
    connect_sensor = ConnectSensor(serial_port=serial_port, baud_rate=baud_rate, width=256, height=288)
    result = connect_sensor.save_fingerprint_into_json(path_json=path_json, name_json=name_json)

    return result


def create_fingerprint_samples_from_sensor(save_as_json: bool = False) -> FingerprintSamples:
    fingerprint_samples = []
    count = 0
    while count < 5:
        sample = get_data_of_fingerprint_from_sensor_in_base64()
        if not isinstance(sample, tuple):
            fingerprint_samples.append(sample)
        else:
            raise Exception("Something wrong occurs during the process")

        count = count + 1

    fingerprint_samples_object = FingerprintSamples(fingerprints=fingerprint_samples)

    if save_as_json:
        save_object_as_json(
            fingerprint_samples_object,
            path_json="./fingerprint_process/data/",
            name_json="fingerprint_samples_base64.json"
        )

    return fingerprint_samples_object


def raw_fingerprint_construction(data_fingerprint: Union[str, List], name_fingerprint: str = "Fingerprint_HTML"):
    raw_data_fingerprint = get_data_fingerprint('api', data_fingerprint)
    if isinstance(raw_data_fingerprint, tuple):
        return raw_data_fingerprint

    fingerprint = Fingerprint(save_result=False, show_result=False, name_fingerprint=name_fingerprint)
    raw_fingerprint = fingerprint.reconstruction_fingerprint(raw_data_fingerprint)

    return raw_fingerprint


def get_quality_of_fingerprint(
        data_fingerprint: Union[str, List],
        name_fingerprint: str = "Fingerprint_HTML",
        return_data: str = "quality"
) -> Union[tuple, str, dict]:
    """
    Get the quality of a fingerprint through of its data represented using base64 or a list of integers

    :param data_fingerprint: (str, list) Data which represent the fingerprint. Can be a str on base64 or a list of int
    :param name_fingerprint: (str) The name of the fingerprint to create. By default, the name is 'Fingerprint_HTML'
    :param return_data: (str) Specify the information to return.
    - **quality** will return the quality ('bad' or 'good') as str
    - **indexes** will return the indexes ('spatial_index' and 'spectral_index') as a dict
    - **full** will return both, the quality and indexes into a dict.
     E.g.
        {'quality': 'good', indexes: {'spatial_index': 0.46, 'spectral_index': 0.65}}

    :return: Return a tuple if an exception occurs, in other case, could return whatever type of data described above
    (str or dict).
    """
    raw_data_fingerprint = get_data_fingerprint('api', data_fingerprint)
    if isinstance(raw_data_fingerprint, tuple):
        return raw_data_fingerprint

    fingerprint = Fingerprint(save_result=False, show_result=False, name_fingerprint=name_fingerprint)
    indexes_dict = fingerprint.get_indexes_of_fingerprint(raw_data_fingerprint)
    quality = fingerprint.get_quality_of_fingerprint(indexes_dict, 'register')

    if return_data == "quality":
        return quality
    elif return_data == "indexes":
        return indexes_dict
    else:
        return {
            'quality': quality,
            'indexes': indexes_dict
        }


def show_fingerprint_image(
        image: Union[ndarray, list, None] = None,
        path: Optional[str] = None,
        title: str = 'Fingerprint'
):
    if image is not None:
        fingerprint_image = Image.fromarray(image)
    elif path is not None:
        fingerprint_image = Image.open(path)
    else:
        return ErrorMessage.NOT_OPTION_FOUND

    fingerprint_image = fingerprint_image.convert("L")
    fingerprint_image.show(title)

    return ErrorMessage.FINGERPRINT_OK


def show_fingerprint_from_array(fingerprint_data, title: str = 'Fingerprint'):
    raw_fingerprint = raw_fingerprint_construction(data_fingerprint=fingerprint_data)
    if isinstance(raw_fingerprint, tuple):
        return ErrorMessage.RECONSTRUCTION_FAILED

    result = show_fingerprint_image(image=raw_fingerprint, title=title)

    return result


def get_data_of_fingerprint_from_sensor_in_base64(source: str = 'sensor') -> Union[str, tuple]:
    connect_sensor = ConnectSensor(serial_port='/dev/ttyUSB0', baud_rate=57600, width=256, height=288)
    data_fingerprint_raw = connect_sensor.catch_data_fingerprint_as_base64(return_mode='str')

    if isinstance(data_fingerprint_raw, tuple):
        if source.lower() == 'api':
            raise compile_exception

    return data_fingerprint_raw


def show_fingerprint_form_base64(image_base64: bytes) -> None:
    image_str = image_base64.decode()

    img = Image.open(io.BytesIO(base64.b64decode(image_str)), formats=["BMP"])

    img.show("Fingerprint from Base64")


def evaluate_preprocessing() -> None:
    base_path = "/home/coffe/Documentos/fintech75_api/fingerprint_process/preprocessing_fingerprints/sampleImages/"
    out_path = "/home/coffe/Documentos/fintech75_api/fingerprint_process/preprocessing_fingerprints/evaluate/"

    change = input(f"Actual path to fetch: {base_path}\n\nChange path?:\n\t[Y]es\n\t[N]o\n\nResponse: ")
    if change.lower().startswith("y"):
        new_path = input("Write the new path: ")
        if not os.path.isdir(new_path):
            print("Not path found")
            return None

        if not new_path.endswith("/"):
            new_path += "/"

        base_path = new_path

    else:
        pass

    int_pattern = r"^[1-9]\d{0,2}$"
    num_samples_str = input("Write the number the samples to be captured: ")
    if re.match(int_pattern, num_samples_str) is not None:
        num_samples = int(num_samples_str)
    else:
        print("Type of value no valid")
        return None

    objects_in_path = os.listdir(base_path)
    files_in_path = [obj for obj in objects_in_path if os.path.isfile(base_path + obj) and obj.endswith(".bmp")]

    if num_samples > len(files_in_path):
        print("There are not sufficient samples")
        return None

    fingerprints = random.sample(files_in_path, num_samples)
    lines = [
        "Sample,Base Spectral,Base Spatial,Valid Reg,Valid Auth,Better Spectral,Better Spatial,Diff Spectral,"
        "Diff Spatial\n"
    ]
    name_fingerprint = "Sample"
    f_obj = Fingerprint(
        name_fingerprint=name_fingerprint,
        show_result=False,
        save_result=False,
        address_image=out_path
    )

    for pos, fingerprint in enumerate(fingerprints):

        actual_name = f"{name_fingerprint}_{pos}"
        img = cv.imread(base_path + fingerprint, 0)

        (base_spectral, base_spatial, valid_reg, valid_auth) = f_obj.evaluate_enhance_process(img, actual_name)

        better_img = cv.imread(out_path + "binary_" + actual_name + ".bmp", 0)
        (better_spectral, better_spatial) = f_obj.get_indexes_of_fingerprint_image(better_img)

        diff_spectral = better_spectral - base_spectral
        diff_spatial = better_spatial - base_spatial
        d_str = f"{actual_name},{base_spectral},{base_spatial},{valid_reg},{valid_auth},{better_spectral}," \
                f"{better_spatial},{diff_spectral},{diff_spatial}\n"
        lines.append(d_str)

    with open(out_path + "result.csv", "w+", encoding='utf-8') as f:
        for line in lines:
            f.write(line)

    print("\n\nThe process have finished :)\n")

    return None


def get_quality_image(
        img_name: str,
        name_fingerprint: str = "sample_fingerprint",
        show_result: bool = True,
        save_result: bool = True
) -> None:
    base_path = "/home/coffe/Documentos/fintech75_api/fingerprint_process/preprocessing_fingerprints/evaluate/"

    change = input(f"Actual path to fetch: {base_path}\n\nChange path?:\n\t[Y]es\n\t[N]o\n\nResponse: ")
    if change.lower().startswith("y"):
        new_path = input("Write the new path: ")
        if not os.path.isdir(new_path):
            print("Not path found")
            return None

        if not new_path.endswith("/"):
            new_path += "/"

        base_path = new_path

    else:
        pass

    img_name += ".bmp" if not img_name.endswith(".bmp") else ""

    img = cv.imread(base_path + img_name, 0)

    quality_image = QualityFingerprint(
        data_filters='dataFilter.txt',
        address_output='./fingerprint_process/data/',
        show_graphs=show_result,
        name_fingerprint=name_fingerprint
    )

    quality_index = quality_image.getQualityFingerprint(img, save_graphs=save_result)
    print(f"Spectral quality of the image: {quality_index}")

    return None


def evaluate_match_tar():
    base_path = "/home/coffe/Documentos/fintech75_api/fingerprint_process/preprocessing_fingerprints/match_test/"
    samples_name = "same_finger"
    base_file = "base.bmp"
    if not os.path.isdir(base_path):
        print("Not path found")
        return None

    objects_in_path = os.listdir(base_path)
    dirs_in_path = [inner_dir for inner_dir in objects_in_path if os.path.isdir(base_path + inner_dir)]
    # print(dirs_in_path)

    lines = ["Sample,True acceptance,False reject,Bad quality\n"]
    count_acceptance = 0
    count_reject = 0
    count_bad_quality = 0
    for inner_dir in dirs_in_path:
        base_finger_path = f"{base_path}{inner_dir}/{base_file}"
        # print(base_finger_path)

        img_base = cv.imread(base_finger_path, 0)
        base_fingerprint = describe_fingerprint_image(img_base)

        if base_fingerprint is None:
            print("An error occurs :(")
            break

        dir_to_fetch = f"{base_path}{inner_dir}/{samples_name}/"
        obj_in_path = os.listdir(dir_to_fetch)
        files_in_path = [obj for obj in obj_in_path if os.path.isfile(dir_to_fetch + obj) and obj.endswith(".bmp")]

        for input_sample in files_in_path:
            # print(dir_to_fetch + input_sample)
            img_input = cv.imread(dir_to_fetch + input_sample, 0)
            input_fingerprint = describe_fingerprint_image(img_input)

            if input_fingerprint is None:
                count_bad_quality += 1
                continue

            if describe_match(base_fingerprint, input_fingerprint):
                count_acceptance += 1
            else:
                count_reject += 1

        lines.append(f"{inner_dir},{count_acceptance},{count_reject},{count_bad_quality}\n")
        count_acceptance = 0
        count_reject = 0
        count_bad_quality = 0

    with open(base_path + "results.csv", "w+", encoding='utf-8') as f:
        for line in lines:
            f.write(line)

    print("\n\n\tThe match process has finished :)\n")

    return None


def evaluate_match_far():
    base_path = "/home/coffe/Documentos/fintech75_api/fingerprint_process/preprocessing_fingerprints/match_test/"
    samples_name = "others_fingers"
    base_file = "base.bmp"
    if not os.path.isdir(base_path):
        print("Not path found")
        return None

    objects_in_path = os.listdir(base_path)
    dirs_in_path = [inner_dir for inner_dir in objects_in_path if os.path.isdir(base_path + inner_dir)]
    # print(dirs_in_path)

    lines = ["Sample,True rejection,False acceptance,Bad quality\n"]
    count_acceptance = 0
    count_reject = 0
    count_bad_quality = 0
    for inner_dir in dirs_in_path:
        base_finger_path = f"{base_path}{inner_dir}/{base_file}"
        # print(base_finger_path)

        img_base = cv.imread(base_finger_path, 0)
        base_fingerprint = describe_fingerprint_image(img_base)

        if base_fingerprint is None:
            print("An error occurs :(")
            break

        dir_to_fetch = f"{base_path}{inner_dir}/{samples_name}/"
        obj_in_path = os.listdir(dir_to_fetch)
        files_in_path = [obj for obj in obj_in_path if os.path.isfile(dir_to_fetch + obj) and obj.endswith(".bmp")]

        for input_sample in files_in_path:
            # print(dir_to_fetch + input_sample)
            img_input = cv.imread(dir_to_fetch + input_sample, 0)
            input_fingerprint = describe_fingerprint_image(img_input)

            if input_fingerprint is None:
                count_bad_quality += 1
                continue

            if describe_match(base_fingerprint, input_fingerprint):
                count_acceptance += 1
            else:
                count_reject += 1

        lines.append(f"{inner_dir},{count_reject},{count_acceptance},{count_bad_quality}\n")
        count_acceptance = 0
        count_reject = 0
        count_bad_quality = 0

    with open(base_path + "results_far.csv", "w+", encoding='utf-8') as f:
        for line in lines:
            f.write(line)

    print("\n\n\tThe match process has finished :)\n")

    return None


def describe_fingerprint_image(img: Union[ndarray, Iterable]) -> Optional[Fingerprint]:
    fingerprint = Fingerprint(
        characteritic_point_thresh=0.8,
        name_fingerprint="fingerprint",
        show_result=False,
        save_result=False,
        min_minutiae=12
    )

    process_message = fingerprint.describe_fingerprint(
        angles_tolerance=1,
        from_image=True,
        fingerprint_image=img,
        mode="auth",
        neighbors_description=False
    )

    if process_message == fingerprint.FINGERPRINT_OK:
        return fingerprint

    fingerprint.show_message(process_message)

    return None


def describe_match(base_fingerprint: Fingerprint, input_fingerprint: Fingerprint) -> bool:
    result = match_index_and_base_fingerprints(
        base_name="base_fingerprint",
        input_name="input_fingerprint",
        mode='core',
        source='api',
        base_fingerprint=base_fingerprint,
        input_fingerprint=input_fingerprint
    )

    if result is True:
        return False

    if result != base_fingerprint.MATCH_FINGERPRINT:
        return False

    return True
