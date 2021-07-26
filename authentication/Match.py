from Matching_Process import Matching_Process
from Matching_Tree import Matching_Tree
from Matching_Core import Matching_Core
from Fingerprint import Fingerprint

def match(base_fingerprint, input_fingerprint, mode='original'):
    base_fingerprint_is_ok = (base_fingerprint != True) and isinstance(base_fingerprint, Fingerprint)
    index_fingerprint_is_ok = (input_fingerprint != True) and isinstance(input_fingerprint, Fingerprint)

    if (base_fingerprint_is_ok and index_fingerprint_is_ok):
        if mode.lower() == 'tree':
            matching = Matching_Tree(local_ratio_tolerance = .1, local_angle_tolerance = 1)
            process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)
        elif mode.lower() == 'original': 
            matching = Matching_Process()
            process_message = matching.matching(base_fingerprint=base_fingerprint, index_fingerprint=input_fingerprint)
        elif mode.lower() == 'core':
            matching = Matching_Core()
            process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)
        else:
            matching = Matching_Core()
            process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)

            if process_message == matching._DONT_MATCH_FINGERPRINT:
                matching = Matching_Tree(local_ratio_tolerance = .1, local_angle_tolerance = 1)
                process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)

        matching.show_message(process_message)
        return process_message
    
    return True 