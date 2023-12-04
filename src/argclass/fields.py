import sys
from typing import Any, TypeVar, overload
from typing import Union

if sys.version_info < (3, 9):
    from typing import Dict, Callable, Sequence
else:
    from collections.abc import Callable, Sequence

    Dict = dict

from .actions import AliasArg, MappingArg
from .core import Arg, Actions, Nargs, missing

__all__ = ['arg', 'posarg', 'vararg', 'arg_mapping', 'arg_alias', 'as_arg']

T = TypeVar('T')


@overload
def arg(*options: str,
        action: Actions = missing,
        nargs: Union[int, Nargs] = missing,
        const=missing,
        default=missing,
        type: Union[type, Callable[[str], T]] = missing,
        validator: Callable[[T], bool] = missing,
        choices: Sequence[str] = missing,
        required: bool = missing,
        hidden: bool = missing,
        help: str = missing,
        group: str = missing,
        ex_group: str = missing,
        metavar: str = missing):
    pass


def arg(*options: str, **kwargs):
    if not all([it.startswith('-') for it in options]):
        raise RuntimeError(f'options should startswith "-". {options}')
    return Arg(*options, **kwargs)


@overload
def posarg(options: str, *,
           nargs: Nargs = None,
           action: Actions = missing,
           const=missing,
           default=missing,
           type: Union[type, Callable[[str], T]] = missing,
           validator: Callable[[T], bool] = missing,
           choices: Sequence[str] = missing,
           help: str = missing,
           group: str = missing,
           ex_group: str = missing):
    pass


def posarg(option: str, *, nargs=None, **kwargs):
    return Arg(metavar=option, nargs=nargs, **kwargs)


@overload
def vararg(options: str, *,
           nargs: Nargs = missing,
           action: Actions = missing,
           const=missing,
           default=missing,
           type: Union[type, Callable[[str], T]] = missing,
           validator: Callable[[T], bool] = missing,
           choices: Sequence[str] = missing,
           help: str = missing,
           group: str = missing,
           ex_group: str = missing):
    pass


def vararg(option: str, *, nargs='*', action='extend', **kwargs):
    return Arg(metavar=option, nargs=nargs, action=action, **kwargs)


@overload
def arg_mapping(*options: str,
                nargs: Union[int, Nargs] = missing,
                const=missing,
                default=missing,
                type: Union[type, Callable[[str], T]] = missing,
                validator: Callable[[T], bool] = missing,
                choices: Sequence[str] = missing,
                required: bool = missing,
                hidden: bool = missing,
                help: str = missing,
                group: str = missing,
                ex_group: str = missing,
                metavar: str = missing):
    pass


def arg_mapping(*options: str, **kwargs):
    if not all([it.startswith('-') for it in options]):
        raise RuntimeError(f'options should startswith "-". {options}')
    return MappingArg(*options, **kwargs)


@overload
def arg_alias(*options: str,
              aliases: Dict[str, Any],
              nargs: Union[int, Nargs] = missing,
              const=missing,
              default=missing,
              type: Union[type, Callable[[str], T]] = missing,
              validator: Callable[[T], bool] = missing,
              choices: Sequence[str] = missing,
              required: bool = missing,
              hidden: bool = missing,
              help: str = missing,
              group: str = missing,
              ex_group: str = missing,
              metavar: str = missing):
    pass


def arg_alias(*options: str, aliases: Dict[str, Any], **kwargs):
    if not all([it.startswith('-') for it in options]):
        raise RuntimeError(f'options should startswith "-". {options}')
    return AliasArg(*options, aliases=aliases, **kwargs)


def as_arg(a) -> Arg:
    if isinstance(a, Arg):
        return a
    raise TypeError
