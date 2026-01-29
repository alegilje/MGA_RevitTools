# encoding: utf-8

import json
from pybase64 import standard_b64decode


def pad_string(s, splitting_symbol, target_length):
    segments = s.split(splitting_symbol)
    while len(splitting_symbol.join(segments)) < target_length:
        segments.append('00')
    return splitting_symbol.join(segments)

def check_stringlenght_add_missing(list, splitting_symbol):
    max_lenght = max(len(s) for s in list)
    normalized_list = [pad_string(s, splitting_symbol, max_lenght) for s in list]
    return normalized_list