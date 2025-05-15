import json
import numpy as np
import os

from . import profanity_types as t

dirname = os.path.dirname(__file__)


def parse_hex_list(hex_array: list[str]) -> list[int]:
    return [int(i, base=16) for i in hex_array]


with open(os.path.join(dirname, "./cl_programs/g_precomp.json")) as f:
    G_PRECOMP = np.array(
        [
            np.array(
                (
                    parse_hex_list(g_i[0]),
                    parse_hex_list(g_i[1]),
                ),
                dtype=t.POINT,
            )
            for g_i in json.load(f)
        ],
    )


with (
    open(os.path.join(dirname, "cl_programs/keccak.cl")) as keccak_code,
    open(os.path.join(dirname, "cl_programs/profanity.cl")) as profanity_code,
):
    OPENCL_PROGRAM = keccak_code.read() + profanity_code.read()
