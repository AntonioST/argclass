import argparse
from typing import Any

from .core import Arg

__all__ = ['AliasArg', 'MappingArg']


class AliasArg(Arg):
    def __init__(self, *options,
                 aliases: dict[str, Any],
                 **kwargs):
        super().__init__(*options, **kwargs)
        self.aliases = aliases

    def add_argument(self, ap: argparse._ActionsContainer, opt):
        kwargs = self.complete_options(opt)

        try:
            ap.add_argument(*self.options, **kwargs, dest=self.attr)
        except TypeError as e:
            if isinstance(opt, type):
                name = opt.__name__
            else:
                name = type(opt).__name__

            raise RuntimeError(f'{name}.{self.attr} : ' + repr(e)) from e

        opt = self.options[0]
        for name, values in self.aliases.items():
            kw = dict(kwargs)
            kw.pop('metavar', None)
            kw.pop('type', None)
            kw['action'] = 'store_const'
            kw['const'] = values
            kw['help'] = f'short for {opt}={values}.'
            ap.add_argument(name, **kw, dest=self.attr)


class MappingArgAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest: str,
                 type=None,
                 choices=None,
                 required: bool = False,
                 help: str = None,
                 metavar: str = None):
        self._type = type
        self._choice = choices

        if metavar is None:
            if choices is None:
                metavar = 'KEY=VALUE'
            else:
                metavar = 'KEY={' + ','.join(choices) + '}'

        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=1,
            default={},
            required=required,
            help=help,
            metavar=metavar)

    def __call__(self,
                 parser: argparse.ArgumentParser,
                 namespace: argparse.Namespace,
                 values: str,
                 option_string: str | None = None) -> None:
        coll = getattr(namespace, self.dest, {})
        if coll is None:
            coll = {}

        value = values[0]
        if '=' in value:
            k, v = value.split('=', 2)
        else:
            k = value
            v = ''

        if self._choice is not None and v not in self._choice:
            raise ValueError(f'{k}={v} not in choice: {self._choice}')

        if self._type is not None:
            v = self._type(v)

        coll[k] = v
        setattr(namespace, self.dest, coll)


class MappingArg(Arg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, action=MappingArgAction, **kwargs)
