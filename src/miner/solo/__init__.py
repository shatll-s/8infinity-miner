import asyncio
import time
from datetime import timedelta
from functools import cached_property
from typing import AsyncGenerator

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from eth_account.types import PrivateKeyType
from eth_typing import HexAddress
from eth_utils import abi_to_signature, keccak, encode_hex
from web3 import AsyncWeb3
from web3.types import EventData

from utils.async_ import async_merge
from utils.ecdsa import get_account_ab, private_key_to_ec_point
from ..base import BaseMiner, Problem
from .constants import (
    ERC20_ABI,
    INFINITY_ADDRESS,
    POW_ABI,
    POW_ADDRESS,
)


class SoloMiner(BaseMiner):
    DATA = "miner-v2".encode()

    def __init__(
        self,
        solver,
        rpc: str,
        ws: str,
        miner_pk: PrivateKeyType,
        poll_problem_interval=0.5,
        reward_recipient: HexAddress | None = None,
    ):
        super().__init__(solver)

        self.miner_account: LocalAccount = Account.from_key(miner_pk)
        w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc, cache_allowed_requests=True))

        self.w3 = w3
        self.w3_ws = AsyncWeb3(AsyncWeb3.WebSocketProvider(ws))
        self.pow = w3.eth.contract(abi=POW_ABI)(POW_ADDRESS)
        self.token = w3.eth.contract(abi=ERC20_ABI)(INFINITY_ADDRESS)
        self.lock = asyncio.Lock()

        self.miner_nonce = None
        self.gas_price = None

        self.poll_problem_interval = poll_problem_interval
        self.reward_recipient = reward_recipient or self.miner_account.address

        self.poll_info_task = asyncio.create_task(self._poll_info())

    async def get_problems(self):
        problem_nonce = None

        async for problem in async_merge(self._listen_problem(), self._poll_problem()):
            nonce, _, _ = problem
            if problem_nonce and problem_nonce >= nonce:
                continue
            problem_nonce = nonce
            yield problem

    async def submit_solution(self, problem, private_key_b):
        async with self.lock:
            nonce, private_key_a, _ = problem
            self.logger.debug(f"Submitting solution for problem #{nonce}")

            t_start = time.time()
            account_ab = get_account_ab(private_key_a, private_key_b)

            public_key_b = private_key_to_ec_point(private_key_b)
            message = self.w3.solidity_keccak(
                ["address", "bytes"], [self.reward_recipient, self.DATA]
            )
            signed_message = account_ab.sign_message(encode_defunct(message))

            tx_params = await self.pow.functions.submit(
                self.reward_recipient, public_key_b, signed_message.signature, self.DATA
            ).build_transaction(
                {
                    "gas": 1_000_000,
                    "from": self.miner_account.address,
                    "nonce": (
                        self.miner_nonce
                        or await self.w3.eth.get_transaction_count(
                            self.miner_account.address
                        )
                    ),
                    "gasPrice": self.gas_price or await self.w3.eth.gas_price,
                }
            )
            self.logger.debug(
                f"Submit transaction prepared in {time.time() - t_start:.2f}s"
            )

            tx_hash = await self.w3.eth.send_raw_transaction(
                self.miner_account.sign_transaction(tx_params).raw_transaction
            )
            self.logger.debug(
                f"Submit tx - {tx_hash.to_0x_hex()} (in {time.time() - t_start:.2f}s, found solution - {account_ab.address})"
            )

            self.gas_price = tx_params["gasPrice"]
            self.miner_nonce = tx_params["nonce"] + 1

    async def flush_stats(self):
        native_balance = (
            await self.w3.eth.get_balance(self.miner_account.address) / 1e18
        )
        token_balance = (
            await self.token.functions.balanceOf(self.reward_recipient).call()
        ) / 1e18
        current_difficulty = await self.pow.functions.difficulty().call()
        current_difficulty_str = current_difficulty.to_bytes(20).hex()
        leading_zeros = len(current_difficulty_str) - len(
            current_difficulty_str.lstrip("0")
        )

        next_submit_timedelta = None
        if self.solver.get_speed() > 0:
            next_submit_timedelta = timedelta(
                seconds=int(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    / (current_difficulty * self.solver.get_speed())
                )
            )

        self.logger.info("| STATS")
        self.logger.info(f"├ hashrate: {self.solver.hashrate()}")
        self.logger.info(f"├ native balance: {native_balance:,.2f} $S")
        self.logger.info(f"├ mined tokens: {token_balance:,.0f} $8")
        self.logger.info(
            f"├ current difficulty: 0x{current_difficulty_str} ({leading_zeros} leading zeros)"
        )

        if next_submit_timedelta is not None:
            self.logger.info(f"├ time to solution ~ {next_submit_timedelta}")

        self.logger.info(f"| ")
        self.logger.info(
            f"└ Miner address: https://sonicscan.org/address/{self.miner_account.address}"
        )

    async def _poll_info(self):
        while True:
            async with self.lock:
                self.miner_nonce = await self.w3.eth.get_transaction_count(
                    self.miner_account.address
                )
                self.gas_price = await self.w3.eth.gas_price
            await asyncio.sleep(1)

    async def _poll_problem(self) -> AsyncGenerator[Problem, None]:
        while True:
            yield await self.pow.functions.currentProblem().call()
            await asyncio.sleep(self.poll_problem_interval)

    async def _listen_problem(self) -> AsyncGenerator[Problem, None]:
        async with self.w3_ws:
            await self.w3_ws.eth.subscribe(
                "logs",
                {
                    "address": POW_ADDRESS,
                    "topics": [self._problem_topic],
                },
            )

            async for log in self.w3_ws.socket.process_subscriptions():
                new_problem: EventData = self.pow.events.NewProblem().process_log(
                    log["result"]
                )
                yield (
                    new_problem["args"]["nonce"],
                    new_problem["args"]["privateKeyA"],
                    new_problem["args"]["difficulty"],
                )

    @cached_property
    def _problem_topic(self):
        return encode_hex(
            keccak(text=abi_to_signature(self.pow.events.NewProblem().abi))
        )
