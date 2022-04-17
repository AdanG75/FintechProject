from fingerprint_process.matching.matching_process import MatchingProcess
from fingerprint_process.matching.matching_tree import MatchingTree
from fingerprint_process.matching.matching_core import MatchingCore
from fingerprint_process.description.fingerprint import Fingerprint


def match(base_fingerprint, input_fingerprint, mode='original'):
    base_fingerprint_is_ok = (base_fingerprint != True) and isinstance(base_fingerprint, Fingerprint)
    index_fingerprint_is_ok = (input_fingerprint != True) and isinstance(input_fingerprint, Fingerprint)

    if (base_fingerprint_is_ok and index_fingerprint_is_ok):
        if mode.lower() == 'tree':
            matching = MatchingTree(local_ratio_tolerance=.1, local_angle_tolerance=1)
            process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)
        elif mode.lower() == 'original':
            matching = MatchingProcess()
            process_message = matching.matching(base_fingerprint=base_fingerprint, index_fingerprint=input_fingerprint)
        elif mode.lower() == 'core':
            matching = MatchingCore()
            process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)
        else:
            matching = MatchingCore()
            process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)

            if process_message == matching.DONT_MATCH_FINGERPRINT:
                matching = MatchingTree(local_ratio_tolerance=.1, local_angle_tolerance=1)
                process_message = matching.matching(base_fingerprint=base_fingerprint,
                                                    input_fingerprint=input_fingerprint)

        matching.show_message(process_message)
        return process_message

    return True
