import asyncio
from typing import AsyncIterator, TypeVar


K = TypeVar("K")


async def async_merge(*async_iters: AsyncIterator[K]) -> AsyncIterator[K]:
    """
    Yield items from all async-iterators as soon as they become available.
    """
    # Kick off one __anext__() call per iterator
    pending = {asyncio.create_task(it.__anext__()): it for it in async_iters}

    while pending:
        # Wait until at least one iterator yields (or raises StopAsyncIteration)
        done, _ = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            it = pending.pop(task)
            try:
                item = task.result()
            except StopAsyncIteration:
                # that iterator is exhausted—don’t reschedule
                continue
            else:
                # yield the item and schedule the next from this iterator
                yield item
                pending[asyncio.create_task(it.__anext__())] = it
