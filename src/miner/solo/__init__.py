import asyncio
from functools import cached_property
from typing import AsyncGenerator

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from eth_account.types import PrivateKeyType
from eth_typing import HexAddress
from eth_utils import abi_to_signature, keccak, encode_hex
from web3 import AsyncWeb3
from web3.middleware import SignAndSendRawMiddlewareBuilder
from web3.types import EventData

from utils.async_ import async_merge
from utils.ecdsa import get_account_ab, private_key_to_ec_point
from ..base import BaseMiner, Problem
from .constants import POW_ADDRESS, POW_ABI


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

        miner_account: LocalAccount = Account.from_key(miner_pk)
        w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc, cache_allowed_requests=True))
        w3.middleware_onion.inject(
            SignAndSendRawMiddlewareBuilder.build(miner_account), layer=0
        )
        w3.eth.default_account = miner_account.address

        self.w3 = w3
        self.w3_ws = AsyncWeb3(AsyncWeb3.WebSocketProvider(ws))
        self.pow = w3.eth.contract(abi=POW_ABI)(POW_ADDRESS)

        self.poll_problem_interval = poll_problem_interval
        self.reward_recipient = reward_recipient or miner_account.address

    async def get_problems(self):
        problem_nonce = None

        async for problem in async_merge(self._listen_problem(), self._poll_problem()):
            nonce, _, _ = problem
            if problem_nonce and problem_nonce >= nonce:
                continue
            problem_nonce = nonce
            yield problem

    async def submit_solution(self, problem, private_key_b):
        _, private_key_a, _ = problem
        account_ab = get_account_ab(private_key_a, private_key_b)

        message = self.w3.solidity_keccak(
            ["address", "bytes"], [self.reward_recipient, self.DATA]
        )
        signed_message = account_ab.sign_message(encode_defunct(message))
        tx_hash = await self.pow.functions.submit(
            self.reward_recipient,
            private_key_to_ec_point(private_key_b),
            signed_message.signature,
            self.DATA,
        ).transact({"gas": 1_000_000})
        self.logger.debug(f"Submit tx - {tx_hash.hex()}")

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
