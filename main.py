import asyncio

from solver.opencl import OpenCLSolver
from miner.solo import SoloMiner

import logging

logging.basicConfig(level=logging.DEBUG)

import os

INFINITY_RPC = os.getenv("INFINITY_RPC", "https://rpc.soniclabs.com")
INFINITY_WS = os.getenv("INFINITY_WS", "wss://rpc.soniclabs.com")
INFINITY_PRIVATE_KEY = os.environ["INFINITY_PRIVATE_KEY"]


async def main():
    miner = SoloMiner(
        OpenCLSolver(),
        rpc=INFINITY_RPC,
        ws=INFINITY_WS,
        miner_pk=INFINITY_PRIVATE_KEY,
    )
    await miner.mine()


asyncio.run(main())
