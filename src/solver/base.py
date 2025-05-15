from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseSolver(ABC):
    @abstractmethod
    async def get_solutions(
        self, private_key_a: int, difficulty: int
    ) -> AsyncGenerator[int, None]: ...

    @abstractmethod
    def get_speed(self) -> float: ...

    def hashrate(self):
        speed = self.get_speed()
        if speed < 1_000:
            return f"{speed:.2f} H/s"
        elif speed < 1_000_000:
            return f"{speed/1_000:.2f} KH/s"
        elif speed < 1_000_000_000:
            return f"{speed/1_000_000:.2f} MH/s"
        elif speed < 1_000_000_000_000:
            return f"{speed/1_000_000_000:.2f} GH/s"
        else:
            return f"{speed/1_000_000_000_000:.2f} TH/s"
