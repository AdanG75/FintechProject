# -*- coding: utf-8 -*
import cv2 as cv
import re

from fingerprint_process.description.fingerprint import Fingerprint
from fingerprint_process.utils import utils as u_fin
from fingerprint_process.utils.error_message import ErrorMessage

# list = []
'''
    gqr - Good Quality Register          : Fingerprint with the minimum quality to be registered
    bqr - Bad Quality Register           : Fingerprint with less quality than the minimum to be registered
    gqa - Good Quality Authentication    : Fingerprint with the minimum quality to be authenticated
    bqa - Bad Quality Authentication     : Fingerprint with less quality than the minimum to be authenticated
    fr  - False Rejection                : Pair of same the fingerprint that is rejected incorrectly
    sm  - Successfully Match             : Pair of same the fingerprint that is accepted correctly
    fm  - False Match                    : Pair of different fingerprints that is accepted incorrectly
    sr  - Successfully Rejection         : Pair of different fingerprints that is rejected correctly
    is  - Impossible State               : Condition which never be happen
'''
states = {'bqr': 0, 'bqa': 0, 'gqr': 0, 'gqa': 0, 'fr': 0, 'sm': 0, 'fm': 0, 'sr': 0, 'is': 0}


def setup():
    path = './fingerprint_process/sampleImages/'
    img_format = '.bmp'
    book = {'names': ['adan', 'anlly', 'getze', 'johan', 'omar', 'viri'],
            'fingers': ['anular', 'indice', 'medio', 'menique', 'pulgar'],
            'sides': ['derecho', 'izquierdo'],
            'numbers': [str(i) for i in range(20)]}

    return book, img_format, path


def check_result(result):
    if isinstance(result, Fingerprint):
        return 1
    elif isinstance(result, int):
        return 0
    else:
        return -1


def open_all_fingerprints(path, image_reference, base_image):
    img = cv.imread(path + image_reference, 0)

    if img is None:
        return False
    else:
        # cv.imshow(base_image + str(count), img)
        # cv.waitKey(0)
        # cv.destroyAllWindows()
        return True


def match_name_image(path, image_reference, base_image):
    img = cv.imread(path + image_reference, 0)

    if img is None:
        return False
    else:
        if re.match(base_image + '.+', image_reference):
            return 1
        else:
            return 0


def describe_match_results(name_match, fingerprint_match):
    em = ErrorMessage()

    if name_match == 1 and fingerprint_match == em.MATCH_FINGERPRINT:
        states['sm'] += 1
    elif name_match == 1 and fingerprint_match != em.MATCH_FINGERPRINT:
        states['fr'] += 1
    elif name_match == 0 and fingerprint_match == em.MATCH_FINGERPRINT:
        states['fm'] += 1
    elif name_match == 0 and fingerprint_match != em.MATCH_FINGERPRINT:
        states['sr'] += 1
    else:
        states['is'] += 1


def match_test(path, image_reference, base_image, fingerprint):
    result = match_name_image(path, image_reference, base_image)

    if result is False:
        # 'Isn't input image into path'
        return False

    input_img = u_fin.get_description_fingerprint(name_fingerprint=image_reference,
                                                  source='image', address_image=(path + image_reference),
                                                  show_result=False, save_result=False)

    result_check = check_result(input_img)
    if result_check == -1:
        # 'Isn't input image into path'
        return False
    elif result_check == 0:
        states['bqa'] += 1
        return True
    else:
        states['gqa'] += 1
        match_result = u_fin.match(base_fingerprint=fingerprint, input_fingerprint=input_img, mode='Full')
        describe_match_results(name_match=result, fingerprint_match=match_result)
        return True


def secuence(func, pattern_name='', fingerprint=None):
    book, img_format, path = setup()
    count = 0
    for name in book['names']:
        for finger in book['fingers']:
            for side in book['sides']:
                for number in book['numbers']:
                    base_image = (name + '_' + finger + '_' + side)
                    image_reference = (base_image + number + img_format)

                    if pattern_name and not pattern_name.isspace():
                        if fingerprint is not None:
                            flag = func(path, image_reference, pattern_name, fingerprint)
                        else:
                            flag = func(path, image_reference, pattern_name)
                    else:
                        flag = func(path, image_reference, base_image)

                    if not flag:
                        break

                    count += 1

        # base_image = ''

    return count


def match_algorithm_analysis(path, image_reference, base_image):
    base_img = u_fin.get_description_fingerprint(name_fingerprint=image_reference,
                                                 source='image', address_image=(path + image_reference),
                                                 show_result=False, save_result=False)

    result_check = check_result(base_img)
    if result_check == -1:
        return False
    elif result_check == 0:
        states['bqr'] += 1
        return True
    else:
        states['gqr'] += 1
        secuence(match_test, base_image, fingerprint=base_img)
        # list.append(result)
        return True


def name_builder():
    # base_image = ''
    # input_image = ''

    # count = secuence(open_all_fingerprints)
    # count = secuence(match_name_image, 'adan_indice_')
    count = secuence(match_algorithm_analysis)

    print(count)
    print(states)
    # print(len(list))
    # print(list)


def test():
    count = secuence(match_algorithm_analysis)

    print(count)
    print(states)
    # name_builder()


if __name__ == '__main__':
    print('Beginning with match tests')
    test()
