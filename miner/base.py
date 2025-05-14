import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator

from solver.base import BaseSolver

Problem = tuple[int, int, int]


class BaseMiner(ABC):
    def __init__(self, solver: BaseSolver):
        self.solver = solver
        self.logger = logging.getLogger(self.__class__.__qualname__)

    @abstractmethod
    def get_problems(self) -> AsyncGenerator[Problem, None]: ...

    @abstractmethod
    async def submit_solution(self, problem: Problem, private_key_b: int): ...

    async def mine(self):
        solver_task = None
        async for problem in self.get_problems():
            if solver_task is not None:
                solver_task.cancel()
            solver_task = asyncio.create_task(self.solve_and_submit(problem))

    async def solve_and_submit(self, problem: Problem):
        _, private_key_a, difficulty = problem
        async for private_key_b in self.solver.get_solutions(private_key_a, difficulty):
            await self.submit_solution(problem, private_key_b)
