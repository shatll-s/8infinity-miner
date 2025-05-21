import time
import asyncio
import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import AsyncGenerator

from solver.base import BaseSolver

Problem = tuple[int, int, int]


def async_retry_infinite(fn):
    @wraps(fn)
    async def wrapper(self: "BaseMiner", *args, **kwargs):
        while True:
            try:
                await fn(self, *args, **kwargs)
            except Exception as e:
                self.logger.info(f"Error in {fn.__qualname__} - {e}")
                self.logger.debug("Details", exc_info=True)

    return wrapper


class BaseMiner(ABC):
    def __init__(self, solver: BaseSolver, flush_stats_every=10):
        self.solver = solver
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.flush_stats_every = flush_stats_every

        self.submit_tasks: set[asyncio.Task] = set()
        self.stats_task = None

    @abstractmethod
    def get_problems(self) -> AsyncGenerator[Problem, None]: ...

    @abstractmethod
    async def _submit_solution(self, problem: Problem, private_key_b: int): ...

    @abstractmethod
    async def flush_stats(self): ...

    @async_retry_infinite
    async def stats_monitor(self):
        while True:
            await asyncio.sleep(
                self.flush_stats_every - time.time() % self.flush_stats_every
            )
            await self.flush_stats()

    @async_retry_infinite
    async def mine(self):
        self.stats_task = asyncio.create_task(self.stats_monitor())

        solver_task = None
        async for problem in self.get_problems():
            for submit_task in self.submit_tasks:
                submit_task.cancel()

            if solver_task is not None:
                solver_task.cancel()
            solver_task = asyncio.create_task(self._solve_and_submit(problem))

    async def _solve_and_submit(self, problem: Problem):
        _, private_key_a, difficulty = problem

        async for private_key_b in self.solver.get_solutions(private_key_a, difficulty):
            self.submit_tasks.add(
                asyncio.create_task(self.submit_solution(problem, private_key_b))
            )

    async def submit_solution(self, problem: Problem, private_key_b: int):
        try:
            return await self._submit_solution(problem, private_key_b)
        except Exception as e:
            self.logger.info(f"Submit solution failed - {e}")
            self.logger.debug("Details", exc_info=True)
