import asyncio

import secrets
import numpy as np
import pyopencl as cl

from utils.async_ import async_merge
from utils.ecdsa import private_key_to_ec_point, add_private_key
from ..base import BaseSolver
from . import profanity_types as t
from .constants import OPENCL_PROGRAM, G_PRECOMP
from .speed_sampler import SpeedSamplerMixin

INVERSE_SIZE = 255
INVERSE_MULTIPLE = 16384


def int_to_ulong4(n: int):
    return np.frombuffer(n.to_bytes(32, byteorder="little"), dtype=np.uint64)


def event_to_future(event):
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    # Callback invoked on COMPLETE status
    def _callback(_):
        loop.call_soon_threadsafe(future.set_result, None)

    # Register callback (callback signature receives event and status)
    event.set_callback(cl.command_execution_status.COMPLETE, _callback)
    return future


async def async_enqueue_copy(queue, dest, src, **kwargs):
    # Enqueue a non-blocking copy
    event = cl.enqueue_copy(queue, dest, src, is_blocking=False, **kwargs)
    # Flush to ensure the command is submitted
    queue.flush()
    # Await completion via callback
    await event_to_future(event)


class Platform(SpeedSamplerMixin):
    def __init__(self, platform: cl.Platform):
        self.ctx = cl.Context(platform.get_devices())
        self.queue = cl.CommandQueue(self.ctx)
        self.program = cl.Program(self.ctx, OPENCL_PROGRAM).build(
            options=[
                "-D",
                f"PROFANITY_INVERSE_SIZE={INVERSE_SIZE}",
                "-D",
                f"MAX_SOLUTIONS={t.MAX_SOLUTIONS}",
            ]
        )

        self.size = INVERSE_SIZE * INVERSE_MULTIPLE

        self.p_delta_x_buf = cl.Buffer(
            self.ctx,
            cl.mem_flags.READ_WRITE | cl.mem_flags.HOST_NO_ACCESS,
            size=self.size * t.MP_NUMBER.itemsize,
        )
        self.p_prev_lambda_buf = cl.Buffer(
            self.ctx,
            cl.mem_flags.READ_WRITE | cl.mem_flags.HOST_NO_ACCESS,
            size=self.size * t.MP_NUMBER.itemsize,
        )
        self.p_inverse_buf = cl.Buffer(
            self.ctx,
            cl.mem_flags.READ_WRITE | cl.mem_flags.HOST_NO_ACCESS,
            size=self.size * t.MP_NUMBER.itemsize,
        )
        self.precomp_buf = cl.Buffer(
            self.ctx,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=G_PRECOMP.astype(t.POINT),
        )
        self.p_result_buf = cl.Buffer(
            self.ctx, cl.mem_flags.READ_WRITE, size=t.RESULT.itemsize
        )

    def _new_problem(self, private_key_a: int, difficulty: int):
        self.round = 1

        self.private_key_a = private_key_a
        self.private_key_b = int(secrets.token_hex(32), base=16)

        self.difficulty_buf = cl.Buffer(
            self.ctx,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.frombuffer(difficulty.to_bytes(20), dtype=np.uint8),
        )
        x, y = private_key_to_ec_point(
            add_private_key(self.private_key_a, self.private_key_b)
        )

        self.program.profanity_init(
            self.queue,
            (self.size,),
            None,
            self.precomp_buf,
            self.p_delta_x_buf,
            self.p_prev_lambda_buf,
            int_to_ulong4(x),
            int_to_ulong4(y),
        )

    def _mine_iteration(self):
        self.round += 1
        self.program.profanity_inverse(
            self.queue,
            (self.size // INVERSE_SIZE,),
            None,
            self.p_delta_x_buf,
            self.p_inverse_buf,
            self.p_result_buf,
        )
        self.program.profanity_iterate(
            self.queue,
            (self.size,),
            None,
            self.p_delta_x_buf,
            self.p_inverse_buf,
            self.p_prev_lambda_buf,
        )
        self.program.score(
            self.queue,
            (self.size,),
            None,
            self.p_inverse_buf,
            self.p_result_buf,
            self.difficulty_buf,
        )

    async def _process_result(self):
        host_result = np.zeros(1, dtype=t.RESULT)
        await async_enqueue_copy(self.queue, host_result, self.p_result_buf)

        num_results, idxs = host_result[0]
        for idx in idxs[:num_results]:
            key_parts = np.zeros(4, dtype=np.uint64)
            key_parts[0] = np.uint64(self.round + 1)
            key_parts[1] = np.uint64(1 + (key_parts[0] < self.round))
            key_parts[2] = np.uint64(1 + (key_parts[1] == 0))
            key_parts[3] = np.uint64(1 + (key_parts[2] == 0) + idx)

            yield add_private_key(
                int("".join(f"{part:016x}" for part in reversed(key_parts)), base=16),
                self.private_key_b,
            )

    async def get_solutions(self, private_key_a: int, difficulty: int):
        self._new_problem(private_key_a, difficulty)

        while True:
            self._mine_iteration()
            async for solution in self._process_result():
                yield solution
            self._speed_sample(self.size)

    @property
    def mining_speed(self):
        return self.speed()


class OpenCLSolver(BaseSolver):
    def __init__(self):
        self.platforms = [Platform(platform) for platform in cl.get_platforms()]

    async def get_solutions(self, private_key_a, difficulty):
        async for solution in async_merge(
            *[
                platform.get_solutions(private_key_a, difficulty)
                for platform in self.platforms
            ]
        ):
            yield solution

    def get_speed(self):
        return sum(platform.mining_speed for platform in self.platforms)
