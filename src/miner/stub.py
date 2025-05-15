import asyncio
import time

from eth_account import Account

from utils.ecdsa import get_account_ab
from .base import BaseMiner

MAGIC_NUMBER = 0x8888888888888888888888888888888888888888
MAX_UINT256 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF


class StubMiner(BaseMiner):

    def __init__(self, solver, target_speed=0.5):
        super().__init__(solver)
        self.submissions = []
        self.target_speed = target_speed
        self.difficulty = MAX_UINT256

    async def get_problems(self):
        while True:
            self.logger.debug(
                f"New problem - difficulty: 0x{self.difficulty.to_bytes(20).hex()}"
            )
            self.solved = asyncio.get_running_loop().create_future()
            yield (0, int.from_bytes(Account.create()), self.difficulty)
            await self.solved

    async def submit_solution(self, problem, private_key_b):
        _, private_key_a, difficulty = problem
        account_ab = get_account_ab(private_key_a, private_key_b)

        if int(account_ab.address, base=16) ^ MAGIC_NUMBER > difficulty:
            return
        self.logger.debug(
            f"New solution: {account_ab.address} (difficulty: 0x{self.difficulty.to_bytes(20).hex()})"
        )

        self.submissions.append(time.monotonic())
        if len(self.submissions) < 20:
            return

        self.submissions = self.submissions[-20:]
        speed = len(self.submissions) / (self.submissions[-1] - self.submissions[0])
        self.difficulty = max(
            int(self.difficulty * (self.target_speed / speed)) % self.MAX_UINT256,
            self.difficulty // 8,
        )
        self.solved.set_result(private_key_b)
