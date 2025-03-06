import math

import numpy as np


def shift_list_with_replacement(lst, shift=1, fill_value=0.0):
    """
    Shifts a list of float values by `shift` positions, replacing NaN values with `fill_value`.

    :param lst: List of float values
    :param shift: Number of positions to shift (positive for right, negative for left)
    :param fill_value: Value to replace NaN or empty slots
    :return: Shifted list with replaced NaN values
    """
    arr = np.array(lst, dtype=float)  # Convert to NumPy array for easier shifting

    if shift > 0:  # Shift right
        arr = np.roll(arr, shift)
        arr[:shift] = fill_value  # Replace the first `shift` elements
    elif shift < 0:  # Shift left
        arr = np.roll(arr, shift)
        arr[shift:] = fill_value  # Replace the last `abs(shift)` elements

    # Replace NaN values with the specified fill_value
    arr = np.nan_to_num(arr, nan=fill_value)

    return arr.tolist()


def truncate(number, decimals=3):
    factor = 10**decimals
    return math.floor(number * factor) / factor
