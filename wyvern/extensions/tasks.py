from __future__ import annotations

import asyncio
import typing

import attrs

__all__: tuple[str, ...] = ("Task", "task")


@attrs.define(kw_only=True, slots=True)
class Task:
    """Represents a task that gets triggerd after some
    interval of time repeatedly."""

    trigger: typing.Callable[..., typing.Awaitable[typing.Any]]
    """The coro to trigger at every interval."""
    delay: float
    """Time delay between triggers ( in seconds )"""
    wait_until_complete: bool = True
    """Weather to wait before one trigger is complete."""
    is_running: bool = False
    """True if the task is running."""

    def update_delay(self, delay: float) -> None:
        self.delay = delay

    async def _runner(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        loop = asyncio.get_event_loop()
        while self.is_running is True:
            if self.wait_until_complete is False:
                loop.create_task(self.trigger(*args, **kwargs))  # type: ignore
            else:
                await self.trigger(*args, **kwargs)
            await asyncio.sleep(self.delay)

    def run(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Starts the task."""
        if self.is_running is False:
            self.is_running = True
        else:
            raise Exception("The task is already running.")
        loop = asyncio.get_event_loop()
        loop.create_task(self._runner(*args, *kwargs))

    def stop(self) -> None:
        """Stops the task."""
        self.is_running = False


def task(
    s: float | None = None, m: float | None = None, h: float | None = None, wait_until_complete: bool = True
) -> typing.Callable[..., Task]:
    """Interface to create a task.

    Parameters
    ----------

    WIP : typing.Any
        Docs to be added.
    """

    def inner(trigger: typing.Callable[..., typing.Awaitable[typing.Any]]) -> Task:
        nonlocal s, m, h
        if (delays := len([item for item in [s, m, h] if item is not None])) > 1 or delays == 0:
            raise ValueError("Only one delay field can be used for the decorator.")
        if s:
            delay = s
        elif m:
            delay = m * 60
        elif h:
            delay = h * 60 * 60

        return Task(
            delay=delay,
            trigger=trigger,
            wait_until_complete=wait_until_complete,
        )

    return inner