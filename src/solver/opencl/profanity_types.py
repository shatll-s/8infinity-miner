import numpy as np

MP_WORDS = 8
MAX_SOLUTIONS = 100

MP_NUMBER = np.dtype([("mp_word", np.uint32, MP_WORDS)])
POINT = np.dtype([("x", MP_NUMBER), ("y", MP_NUMBER)])
RESULT = np.dtype(
    [
        ("numFound", np.uint32),
        ("foundIds", np.uint32, MAX_SOLUTIONS),
    ]
)
