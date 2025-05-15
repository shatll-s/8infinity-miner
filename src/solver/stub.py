from utils.ecdsa import get_account_ab
from .base import BaseSolver

MAGIC_NUMBER = 0x8888888888888888888888888888888888888888


class StubSolver(BaseSolver):
    async def get_solutions(self, private_key_a, difficulty):
        private_key_b = 0
        while True:
            account_ab = get_account_ab(private_key_a, private_key_b)
            if int(account_ab.address, base=16) ^ MAGIC_NUMBER < difficulty:
                yield private_key_b

            private_key_b += 1

    def get_speed(self):
        return 0.0
