import asyncio

from solver.base import BaseSolver
from solver.opencl import OpenCLSolver

from eth_account import Account
from eth_keys.constants import SECPK1_N


async def print_hashrate(solver: BaseSolver):
    while True:
        await asyncio.sleep(1)
        print(f"Current hashrate: {solver.hashrate()}")


async def main():
    solver = OpenCLSolver()
    t = asyncio.create_task(print_hashrate(solver))

    private_key_a = 23408923049283
    async for private_key_b in solver.get_solutions(
        private_key_a, 0x00000888888888888888888888888888888888888
    ):
        private_key_ab = (private_key_a + private_key_b) % SECPK1_N
        account_ab = Account.from_key(private_key_ab.to_bytes(32))
        print(account_ab.address)


asyncio.run(main())
