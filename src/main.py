import asyncio

import config
from solver.opencl import OpenCLSolver
from miner.solo import SoloMiner


async def main():
    miner = SoloMiner(
        OpenCLSolver(),
        rpc=config.RPC,
        ws=config.WS,
        miner_pk=config.MINER_PRIVATE_KEY,
        reward_recipient=config.REWARDS_RECIPIENT_ADDRESS,
    )
    await miner.mine()


asyncio.run(main())
