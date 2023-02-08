# -*- coding: utf-8 -*-
from controller.test.test_sign_up import test_register_fingerprint
from core.config import charge_settings
from fingerprint_process.utils import utils as u_fin
from fingerprint_process.utils.error_message import ErrorMessage
from fingerprint_process.description.fingerprint import Fingerprint
from web_utils.image_on_web import open_fingerprint_data_from_json, save_fingerprint_in_memory


def local_test():
    print('\n\tAuthentication\'s Module\n')
    print('\nOptions:\n')
    print('\t1.- Create fingerprint\'s bank')
    print('\t2.- Fingerprints processing flow (from Sensor)')
    print('\t3.- Fingerprints processing flow (from Image)')
    print('\t4.- Fingerprints Matching process (from Sensor)')
    print('\t5.- Fingerprints Matching process (from Image)')
    print('\t6.- Fingerprints Matching tree process (from Sensor)')
    print('\t7.- Fingerprints Matching tree process (from Image)')
    print('\t8.- Fingerprints Matching Core (from Sensor)')
    print('\t9.- Fingerprints Matching Core (from Image)')
    print('\tA.- Save fingerprint into JSON')
    print('\tB.- Show fingerprint from JSON')
    print('\tC.- Show fingerprint from Base64')
    print('\tD.- Get fingerprint on Base64')
    print('\tE.- Create FingerprintSamples request within a json file')
    print('\tF.- Test of register fingerprint')
    print('\tG.- Capture good quality fingerprints')
    print('\tH.- Evaluate preprocessing')
    print('\tI.- Get quality of image')
    print('\tJ.- Evaluate TAR in Match')
    print('\tK.- Evaluate FAR in Match')
    print('\tX.- Exit the programme')

    print('\n')
    option = input('Select an option: ')

    if option == '1':
        u_fin.create_fingerprint_samples()

    elif option == '2':
        result = u_fin.get_description_fingerprint()

        if not isinstance(result, Fingerprint):
            return True
        else:
            result.show_characteristic_point_from_list(type_characteristic_point='minutiae')
            result.show_characteristic_point_from_list(type_characteristic_point='core')

    elif option == '3':
        result = u_fin.get_description_fingerprint(name_fingerprint='my_fingerprint', source='image')
        if not isinstance(result, Fingerprint):
            return True
        else:
            result.show_characteristic_point_from_list(type_characteristic_point='minutiae', mode='full')
            result.show_characteristic_point_from_list(type_characteristic_point='core')

    elif option == '4':
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_S', 'index_fingerprint_S',
                                                             mode='original', source='sensor')
        if fail_match == True:
            return fail_match

    elif option == '5':
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_I', 'index_fingerprint_I',
                                                        mode='original', source='image')
        if fail_match == True:
            return fail_match

    elif option == '6':
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_S_tree_', 'input_fingerprint_S_tree_',
                                                             mode='tree', source='sensor')
        if fail_match == True:
            return fail_match

    elif option == '7':
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_I_tree_', 'input_fingerprint_I_tree_',
                                                             mode='tree', source='image')
        if fail_match == True:
            return fail_match

    elif option == '8':
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_S_core_', 'input_fingerprint_S_core_',
                                                             mode='core', source='sensor')
        if fail_match == True:
            return fail_match

    elif option == '9':
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_I_core_', 'input_fingerprint_I_core_',
                                                             mode='core', source='image')
        if fail_match == True:
            return fail_match

    elif option.lower() == 'a':
        result = u_fin.save_fingerprint_into_json()

        if isinstance(result, tuple):
            return True

        if isinstance(result, dict):
            print(result)

    elif option.lower() == 'b':
        fingerprint_data = open_fingerprint_data_from_json()
        result = u_fin.show_fingerprint_from_array(fingerprint_data)

        if not result == ErrorMessage.FINGERPRINT_OK:
            console = ErrorMessage()
            console.show_message(result)

    elif option.lower() == 'c':
        fingerprint_data = open_fingerprint_data_from_json()
        image_base64 = save_fingerprint_in_memory(data_fingerprint=fingerprint_data)
        u_fin.show_fingerprint_form_base64(image_base64)

    elif option.lower() == 'd':
        fingerprint_data_base64 = u_fin.get_data_of_fingerprint_from_sensor_in_base64()
        if isinstance(fingerprint_data_base64, tuple):
            print('Some error occurs during process')
            return True

        print(fingerprint_data_base64)

    elif option.lower() == 'e':
        u_fin.create_fingerprint_samples_from_sensor(save_as_json=True)

    elif option.lower() == 'f':
        test_register_fingerprint()

    elif option.lower() == 'g':
        u_fin.capture_good_quality_fingerprints()

    elif option.lower() == 'h':
        u_fin.evaluate_preprocessing()

    elif option.lower() == 'i':
        name_img = input("Write the name of the image to open: ")
        u_fin.get_quality_image(name_img)

    elif option.lower() == 'j':
        u_fin.evaluate_match_tar()

    elif option.lower() == 'k':
        u_fin.evaluate_match_far()

    elif option.lower() == 'x':
        return True

    elif (option == '\n') or (option == ''):
        pass

    else:
        print('\n:: Option can not be find it ::\n')

    return False


if __name__ == '__main__':
    settings = charge_settings()
    while True:
        end_programme = local_test()
        if end_programme:
            print('\n\tGood bye :)\n')
            break
