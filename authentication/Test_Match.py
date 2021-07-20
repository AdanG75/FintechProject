# -*- coding: utf-8 -*


def setup():
    
    path = './authentication/sampleImages/'
    img_format = '.bmp'
    book = { 'names': ['adan', 'anlly', 'getze', 'viri'], 
            'fingers': ['anular', 'indice', 'medio', 'menique', 'pulgar'],
            'sides': ['derecho', 'izquierdo'],
            'numbers': [str(i) for i in range(20)] }

    return book, img_format, path


def name_builder():
    book, img_format, path = setup()

    base_image = ''
    input_image = ''

    for name in book['names']:
        for finger in book['fingers']:
            for side in book['sides']:
                for number in book['numbers']:
                    base_image = (name + '_' + finger + '_' + side)
                    image_reference = (base_image + number + img_format)

                    print (image_reference)
        
        base_image = ''

def test():
    name_builder()


if __name__ == '__main__':
    test()