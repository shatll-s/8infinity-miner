import asyncio

from solver.stub import StubSolver
from solver.opencl import OpenCLSolver
from miner.stub import StubMiner

import logging

logging.basicConfig(level=logging.DEBUG)


async def main():
    miner = StubMiner(OpenCLSolver())
    miner.difficulty = (
        0x0000088888888888888888888888888888888888  # real difficulty emulation
    )
    await miner.mine()


asyncio.run(main())
