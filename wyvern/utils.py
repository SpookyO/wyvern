from __future__ import annotations

import ast
import datetime
import typing

import attrs


class Empty:
    ...


EMPTY = Empty()


def create_timestamp(dt: datetime.datetime | datetime.timedelta, *, style: str = "t") -> str:
    """Creates an UNIX timestamp for provided datetime or timedelta object.
    
    Parameters
    ----------

    dt : datetime.datetime | datetime.timedelta
        The datetime or timedelta to convert.
    
    Returns
    -------

    str 
        The UNIX timestamp.
    """
    if isinstance(dt, datetime.timedelta):
        dt = datetime.datetime.utcnow() + dt
    return f"<t:{int(dt.timestamp())}:{style}>"


@attrs.define(kw_only=True)
class CacheConfigurations:
    users: bool = True
    guilds: bool = True
    members: bool = True
    roles: bool = True
    channels: bool = True
    messages: bool = False


@attrs.define
class Hook:
    """Hooks for per-module setup. They can be loaded using `GatewayClient.load_hooks`"""
    callback: typing.Callable[..., typing.Any]
    """Callback of the hook."""
    name: str
    """Name of the hook."""

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return self.callback(*args, **kwargs)


def as_hook(name: str | None = None) -> typing.Callable[..., Hook]:
    """Creates a [wyvern.utils.Hook][]
    
    Parameters
    ----------
    
    name : str
        Name of the hook.

    Returns
    -------

    wyvern.utils.Hook
        The hook that was created.
    """
    def inner(callback: typing.Callable[..., typing.Any]) -> Hook:
        return Hook(callback, name or callback.__name__)

    return inner


class Eval:
    """Class for code evaluation.

    !!! warning
        This class is not sandboxed so data like environmental variables
        will be evaluated when the methods gets executed as well.

    """

    def add_returns(self, body: typing.Any) -> None:
        if isinstance(body[-1], ast.Expr):
            body[-1] = ast.Return(body[-1].value)
            ast.fix_missing_locations(body[-1])

        # for if statements, we insert returns into the body and the orelse
        if isinstance(body[-1], ast.If):
            self.add_returns(body[-1].body)
            self.add_returns(body[-1].orelse)

        # for with blocks, again we insert returns into the body
        if isinstance(body[-1], ast.With):
            self.add_returns(body[-1].body)

    async def f_eval(self, *, code: str, renv: dict[str, typing.Any]) -> typing.Any:
        """Evaluates the code in the bot's namespace.

        Parameters
        ----------

        code : str
            The code to evaluate.
        renv: dict[str, typing.Any]
            Environment to evaluate code in.

        Returns
        -------

        typing.Any
            The result of the code.

        """
        _fn_name = "__wyvern_eval"
        code = "\n".join(f"    {i}" for i in code.strip().splitlines())
        parsed: typing.Any = ast.parse(f"async def {_fn_name}:\n{code}")
        self.add_returns(parsed.body[0].body)
        exec(compile(parsed, filename="<ast>", mode="exec"), renv)
        fn = renv[_fn_name]
        return await fn()