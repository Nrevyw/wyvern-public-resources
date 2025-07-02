import numpy as np


def min_max_normalize(arr: np.ndarray) -> np.ndarray:
    # nanmin/nanmax ignore NaN values within an array while still calculating the value (max, min)
    return (arr - np.nanmin(arr)) / (np.nanmax(arr) - np.nanmin(arr))
