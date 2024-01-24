import abc
import argparse
import collections
import sys
from collections.abc import Iterable, Sequence, Callable
from typing import Any, TypeVar, Literal, overload, get_origin, get_args, get_type_hints, Type

from typing_extensions import Self

from .validator import bool_type, ann_type

__all__ = [
    'AbstractOptions',
    'new_parser',
    'new_command_parser',
    'parse_args',
    'parse_command_args',
    'set_options',
    'copy_args',
    'set_ext_options',
    'with_defaults',
    'print_help',
    'as_dict'
]

T = TypeVar('T')
missing = object()
Nargs = Literal[
    '*', '+', '?', '...'
]
Actions = Literal[
    'store',
    'store_const',
    'store_true',
    'store_false',
    'append',
    'append_const',
    'extend',
    'count',
    'help',
    'version',
        #
    'boolean'
]


class ArgumentParser(argparse.ArgumentParser):
    exit_status = 0
    exit_message = None

    def exit(self, status: int = 0, message: str = None):
        self.exit_status = status
        self.exit_message = message

    def error(self, message: str):
        self.exit_status = 2
        self.exit_message = message


class AbstractOptions(metaclass=abc.ABCMeta):
    """Abstract Option class.

    Class document in subclass would be taken as :attr:`ArgumentParser.description`.
    """

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        with_defaults(obj)
        return obj

    def __init__(self, ref: T | None = None, **kwargs):
        if ref is not None:
            copy_args(self, ref, **kwargs)

    def main(self, args: list[str] = None, *,
             parse_only=False,
             system_exit: bool | type[BaseException] = True) -> int:
        """

        :param args:
        :param parse_only: only parse input. don't raise any error. return 0 when success.
        :param system_exit: raise SystemExit when return code is non-zero (include parsing error).
        :return:
        """
        ap = self.new_parser(reset=True)
        res = ap.parse_args(args)
        set_options(self, res)

        if parse_only:
            return ap.exit_status

        if ap.exit_status != 0 and system_exit:
            if system_exit is True:
                ap.print_usage(sys.stderr)
                print(ap.exit_message, file=sys.stderr)
                sys.exit(ap.exit_status)
            else:
                raise system_exit(ap.exit_status)

        if (ret := self.run()) is None:
            ret = 0

        if system_exit:
            # force exit for sometimes __main__ doesn't wrap exit code with sys.exit
            if system_exit is True:
                sys.exit(ret)
            else:
                raise system_exit(ap.exit_status)

        return ret

    @abc.abstractmethod
    def run(self) -> int | None:
        pass

    @classmethod
    def new_parser(cls, **kwargs) -> ArgumentParser:
        return new_parser(cls, **kwargs)

    @classmethod
    def parser_usage(cls) -> str | list[str] | None:
        return None

    @classmethod
    def parser_epilog(cls) -> str | None:
        return None

    @classmethod
    def print_help(cls) -> str:
        from io import StringIO
        buf = StringIO()
        cls.new_parser().print_help(file=buf)
        return buf.getvalue()

    @classmethod
    def print_usage(cls) -> str:
        from io import StringIO
        buf = StringIO()
        cls.new_parser().print_usage(file=buf)
        return buf.getvalue()

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        """key value pair content"""
        self_type = type(self)
        ret = []
        for a_name in dir(self_type):
            a_value = getattr(self_type, a_name)
            if isinstance(a_value, Arg) and not a_name.startswith('_'):
                try:
                    ret.append(f'{a_name} = {a_value.__get__(self, self_type)}')
                except:
                    ret.append(f'{a_name} = <error>')
            elif isinstance(a_value, property):
                try:
                    ret.append(f'{a_name} = {a_value.__get__(self, self_type)}')
                except:
                    ret.append(f'{a_name} = <error>')

        return '\n'.join(ret)


class Arg(object):
    __match_args__ = ()

    def __init__(self, *options,
                 validator: Callable[[T], bool] = None,
                 group: str = None,
                 ex_group: str = None,
                 hidden: bool = False,
                 **kwargs):
        self.attr = None
        self.attr_type = Any
        self.group = group
        self.ex_group = ex_group
        self.validator = validator
        self.options = options
        self.hidden = hidden
        self.kwargs = kwargs

    @property
    def default(self) -> Any:
        try:
            return self.kwargs['default']
        except KeyError:
            pass

        if (action := self.kwargs.get('action', None)) == 'store_true':
            return False
        elif action == 'store_false':
            return True
        elif self.attr_type == bool:
            return False

        return missing

    @property
    def const(self) -> Any:
        try:
            return self.kwargs['const']
        except KeyError as e:
            pass

        if (action := self.kwargs.get('action', None)) == 'store_true':
            return True
        elif action == 'store_false':
            return False
        elif self.attr_type == bool:
            return True

        return missing

    @property
    def metavar(self) -> str | None:
        return self.kwargs.get('metavar', None)

    @property
    def choices(self) -> tuple[str, ...] | None:
        return self.kwargs.get('choices', None)

    @property
    def required(self) -> bool:
        return self.kwargs.get('required', False)

    @property
    def type(self) -> type | Callable[[str], T]:
        try:
            return self.kwargs['type']
        except KeyError:
            pass

        attr_type = self.attr_type
        if attr_type == bool:
            return bool_type
        elif attr_type in (str, int, float):
            return attr_type
        else:
            return ann_type(self.attr, attr_type)

    def cast(self, value: str) -> T:
        ret = self.type(value)
        if self.validator is not None:
            if not self.validator(ret):
                raise ValueError(value)
        return ret

    @property
    def help(self) -> str | None:
        return self.kwargs.get('help', None)

    def __set_name__(self, owner: type, name: str):
        self.attr = name
        self.attr_type = get_type_hints(owner).get(name, Any)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        try:
            return instance.__dict__[f'__{self.attr}']
        except KeyError:
            pass

        raise AttributeError

    def __set__(self, instance, value):
        instance.__dict__[f'__{self.attr}'] = value

    def __delete__(self, instance):
        try:
            del instance.__dict__[f'__{self.attr}']
        except KeyError:
            pass

    def add_argument(self, ap: argparse._ActionsContainer, owner):
        kwargs = self.complete_options(owner)

        try:
            ap.add_argument(*self.options, **kwargs, dest=self.attr)
        except TypeError as e:
            if isinstance(owner, type):
                name = owner.__name__
            else:
                name = type(owner).__name__

            raise RuntimeError(f'{name}.{self.attr} : ' + repr(e)) from e

    def complete_options(self, owner) -> dict[str, Any]:
        attr_type = self.attr_type
        kwargs = dict(self.kwargs)

        if len(self.options) == 0:  # positional argument
            if 'default' not in kwargs:
                kwargs.setdefault('nargs', '?')

        if 'type' not in kwargs:
            if attr_type == bool and 'default' not in kwargs:
                if 'nargs' in kwargs:
                    kwargs['type'] = bool_type
                    kwargs['action'] = 'store'
                else:
                    kwargs.setdefault('action', 'store_true')
                    kwargs.setdefault('default', False)

            if get_origin(attr_type) is list:
                kwargs.setdefault('action', 'append')
            else:
                kwargs.setdefault('action', 'store')

            if kwargs['action'] in ('store', 'store_const'):  # value type
                kwargs['type'] = ann_type(self.attr, attr_type)
                if get_origin(attr_type) == Literal and 'metavar' not in kwargs:
                    kwargs['metavar'] = '|'.join(get_args(attr_type))
            elif kwargs['action'] in ('append', 'append_const', 'extend'):  # collection type
                kwargs.setdefault('default', get_origin(attr_type)())

                a_type_arg = get_args(attr_type)  # Coll[T]
                if len(a_type_arg) == 0:
                    kwargs['type'] = attr_type
                elif len(a_type_arg) == 1:
                    kwargs['type'] = ann_type(self.attr, a_type_arg[0])
                else:
                    raise RuntimeError()

        if self.validator is not None:
            kwargs['type'] = validator(kwargs['type'], self.validator)

        if self.hidden:
            kwargs['help'] = argparse.SUPPRESS

        return kwargs

    def set_default(self, value, omit_value=missing) -> Self:
        """Set the default value. This method help to build optional value arg,
        which its value can be omitted.

        Overwrite attribute default, const and nargs.

        :param value: value used when the arg isn't presented
        :param omit_value: value used when value is omitted.
        :return:
        """
        kwargs = dict(self.kwargs)
        if omit_value is missing:
            kwargs['default'] = value
            kwargs['nargs'] = 1
            try:
                del kwargs['const']
            except KeyError:
                pass
        else:
            kwargs['default'] = value
            kwargs['const'] = omit_value
            kwargs['nargs'] = '?'

        return Arg(
            *self.options,
            group=self.group,
            ex_group=self.ex_group,
            validator=self.validator,
            **kwargs
        )

    @overload
    def with_options(self,
                     option: str | dict[str, str] = None,
                     *options: str,
                     action: Actions = None,
                     nargs: int | Nargs = None,
                     const: T = None,
                     default: T = None,
                     type: Type | Callable[[str], T] | None = None,
                     validator: Callable[[T], bool] = None,
                     choices: Sequence[str] = None,
                     required: bool = None,
                     hidden: bool = None,
                     help: str = None,
                     group: str = None,
                     ex_group: str = None,
                     metavar: str = None) -> Self:
        pass

    def with_options(self, *options, **kwargs) -> Self:
        """Modify or update keyword parameter and return a new argument.

        option flags update rule:

        1. `()` : do not update options
        2. `('-a', '-b')` : replace options
        3. `(..., '-c')` : append options
        4. `({'-a': '-A'})` : rename options
        4. `({'-a': '-A'}, ...)` : rename options, keep options if not in the dict.

        general form:

        `() | (dict?, ...?, *str)`

        :param options: change option flags
        :param kwargs: change keyword parameters, use `...` to unset parameter
        :return:
        """
        kw = dict(self.kwargs)
        kw['group'] = self.group
        kw['ex_group'] = self.ex_group
        kw['validator'] = self.validator
        kw['hidden'] = self.hidden
        kw.update(kwargs)

        for k in list(kw.keys()):
            if kw[k] is ...:
                del kw[k]

        cls = type(self)

        if len(self.options) > 0:
            match options:
                case ():
                    return cls(*self.options, **kw)
                case (a, *o) if a is ...:
                    return cls(*self.options, *o, **kw)
                case (dict(mapping), ):
                    return cls(*self._map_options(mapping, False), **kw)
                case (dict(mapping), a) if a is ...:
                    return cls(*self._map_options(mapping, True), **kw)
                case (dict(mapping), a, *o) if a is ...:
                    return cls(*self._map_options(mapping, True), *o, **kw)
                case (dict(mapping), *o):
                    return cls(*self._map_options(mapping, False), *o, **kw)
                case _:
                    return cls(*options, **kw)
            # if len(options) == 0:
            #     return cls(*self.options, **kw)
            # elif options[0] is ...:
            #     return cls(*self.options, *options[1:], **kw)
            # elif isinstance(options[0], dict):
            #     if len(options) == 1:
            #         return cls(*self._map_options(options[0], False), **kw)
            #     if len(options) == 2 and options[1] is ...:
            #         return cls(*self._map_options(options[0], True), **kw)
            #     if options[1] is ...:
            #         return cls(*self._map_options(options[0], True), *options[2:], **kw)
            #     else:
            #         return cls(*self._map_options(options[0], False), *options[1:], **kw)
            # else:
            #     return cls(*options, **kw)

        else:
            if len(options) > 0:
                raise RuntimeError('cannot change positional argument to optional')

            return cls(**kw)

    def _map_options(self, mapping: dict[str, str], keep: bool) -> list[str]:
        new_opt = []
        for old_opt in self.options:
            try:
                new_opt.append(mapping[old_opt])
            except KeyError:
                if keep:
                    new_opt.append(old_opt)
        return new_opt


def validator(type_caster: Callable[[str], T], validator: Callable[[T], bool]) -> T:
    """validator combined type caster.

    :param type_caster: value type caster
    :param validator: value validator
    :return: type caster
    """

    def _type(value: str):
        value = type_caster(value)
        if not validator(value):
            raise TypeError
        return value

    return _type


def foreach_arguments(opt: T | type[T]) -> Iterable[Arg]:
    if isinstance(opt, type):
        clazz = opt
    else:
        clazz = type(opt)

    arg_set = set()
    for clz in reversed(clazz.mro()):
        if (ann := getattr(clz, '__annotations__', None)) is not None:
            for attr in ann:
                if isinstance((arg := getattr(clazz, attr, None)), Arg) and attr not in arg_set:
                    arg_set.add(attr)
                    yield arg


def new_parser(opt: T | type[T], reset=False,
               group_order_list: list[str] = None,
               **kwargs) -> ArgumentParser:
    """

    :param opt:
    :param reset: reset *opt*'s argument values
    :param kwargs: keywords for ArgumentParser
    :return: ArgumentParser
    """
    kwargs.setdefault('formatter_class', argparse.RawTextHelpFormatter)

    opt_type = opt if isinstance(opt, type) else type(opt)

    if issubclass(opt_type, AbstractOptions):
        if 'description' not in kwargs and opt_type.__doc__ is not None:
            kwargs['description'] = opt_type.__doc__

        if 'epilog' not in kwargs:
            if (epilog := opt_type.parser_epilog()) is not None:
                kwargs['epilog'] = epilog

        if 'usage' not in kwargs:
            if (usage := opt_type.parser_usage()) is not None:
                if isinstance(usage, list):
                    usage = '\n'.join(['\t' + it for it in usage])
                kwargs['usage'] = usage

    ap = ArgumentParser(**kwargs)

    gp: dict[str, list[Arg]] = collections.defaultdict(list)
    eg: dict[tuple[str | None, str], argparse._ActionsContainer] = {}

    #
    for arg in foreach_arguments(opt):
        if not isinstance(opt, type) and reset:
            arg.__delete__(opt)

        if arg.group is not None:
            gp[arg.group].append(arg)
            continue
        elif arg.ex_group is not None:
            try:
                tp = eg[(None, arg.ex_group)]
            except KeyError:
                eg[(None, arg.ex_group)] = tp = ap.add_mutually_exclusive_group()
        else:
            tp = ap

        arg.add_argument(tp, opt)

    # group arguments, for ordered groups
    for group in (group_order_list or []):
        if (args := gp.pop(group, None)) is not None:
            pp = ap.add_argument_group(group)
            for arg in args:
                tp = pp

                if arg.ex_group is not None:
                    try:
                        tp = eg[(group, arg.ex_group)]
                    except KeyError:
                        eg[(group, arg.ex_group)] = tp = tp.add_mutually_exclusive_group()

                arg.add_argument(tp, opt)

    # group arguments, for left groups
    for group, args in gp.items():
        tp = ap.add_argument_group(group)
        for arg in args:
            arg.add_argument(tp, opt)

    return ap


def new_command_parser(parsers: dict[str, AbstractOptions | type[AbstractOptions]],
                       usage: str = None,
                       description: str = None,
                       reset=False) -> ArgumentParser:
    ap = ArgumentParser(
        usage=usage,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sp = ap.add_subparsers()

    for cmd, pp in parsers.items():
        ppap = new_parser(pp, reset=reset)
        ppap.set_defaults(main=pp)
        sp.add_parser(cmd, help=pp.__doc__, parents=[ppap], add_help=False)

    return ap


def set_options(opt: T, res: argparse.Namespace):
    for arg in foreach_arguments(opt):
        try:
            value = getattr(res, arg.attr)
        except AttributeError:
            pass
        else:
            arg.__set__(opt, value)


def parse_args(opt: T, args: list[str] = None) -> T:
    ap = new_parser(opt, reset=True)
    res = ap.parse_args(args)
    set_options(opt, res)
    return opt


def parse_command_args(parsers: dict[str, AbstractOptions | type[AbstractOptions]],
                       args: list[str] = None,
                       usage: str = None,
                       description: str = None,
                       run_main=True) -> AbstractOptions | None:
    ap = new_command_parser(parsers, usage, description, reset=True)
    res = ap.parse_args(args)

    pp: AbstractOptions = getattr(res, 'main', None)
    if isinstance(pp, type):
        pp = pp()

    if pp is not None:
        set_options(pp, res)

    if run_main:
        if pp is not None:
            pp.run()
        else:
            print(f'Should be one of {", ".join(parsers.keys())}')

    return pp


def print_help(opt: T):
    new_parser(opt).print_help(sys.stdout)


def with_defaults(opt: T) -> T:
    for arg in foreach_arguments(opt):
        if (value := arg.default) is missing:
            arg.__delete__(opt)
        else:
            # print('set_default', arg.attr, value)
            arg.__set__(opt, value)

    return opt


def copy_args(opt: T, ref: Any, **kwargs) -> T:
    """copy arguments from *ref* to *opt*

    :param opt: target
    :param ref: source
    :param kwargs: overwrite arguments
    :return: *opt*
    """
    shadow = ShadowOption(ref, **kwargs)

    for arg in foreach_arguments(opt):
        try:
            value = getattr(shadow, arg.attr)
        except AttributeError:
            pass
        else:
            if isinstance(value, str):
                value = arg.cast(value)
            # print('set', arg.attr, value)
            arg.__set__(opt, value)
    return opt


def set_ext_options(opt: T, args: dict[str, Any | None],
                    protected: list[str] | dict[str, Any | None] = None) -> T:
    """

    :param opt:
    :param args:
    :param protected:
    :return:
    """
    for arg in foreach_arguments(opt):
        if (attr := arg.attr).startswith('_'):
            attr = attr[1:]

        if protected is not None and attr in protected:
            if isinstance(protected, list):
                continue
            if isinstance(protected, dict) and protected[attr] is not None:
                continue

        if (value := args.get(attr, missing)) is not missing:
            if value is None:
                arg.__delete__(opt)
            else:
                if isinstance(value, str):
                    value = arg.cast(value)

                # print(arg.attr, '=', value)
                arg.__set__(opt, value)
    return opt


def as_dict(opt: T) -> dict[str, Any]:
    ret = {}
    for arg in foreach_arguments(opt):
        try:
            value = arg.__get__(opt)
        except AttributeError:
            pass
        else:
            ret[arg.attr] = value
    return ret


class ShadowOption:
    """Shadow options, used to pass wrapped :class:`AbstractOptions`
    """

    def __init__(self, ref: Any, **kwargs):
        self.__ref = ref
        self.__kwargs = kwargs

    def __getattr__(self, attr: str):
        if attr in self.__kwargs:
            return self.__kwargs[attr]

        if attr.startswith('_') and attr[1:] in self.__kwargs:
            return self.__kwargs[attr[1:]]

        if hasattr(self.__ref, attr):
            return getattr(self.__ref, attr)

        raise AttributeError(attr)
