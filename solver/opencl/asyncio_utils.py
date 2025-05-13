import asyncio
from typing import AsyncIterator, TypeVar

import pyopencl as cl


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


def event_to_future(event):
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    # Callback invoked on COMPLETE status
    def _callback(_status):
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
