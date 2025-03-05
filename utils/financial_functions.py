import math


def truncate(number, decimals=3):
    factor = 10**decimals
    return math.floor(number * factor) / factor
