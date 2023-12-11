from collections.abc import Callable
from typing import TypeVar, get_origin, Any, Literal, get_args, Union, overload

__all__ = [
    'literal_value_type',
    'bool_type',
    'union_type',
    'ann_type',
    'tuple_type',
    'list_type',
    'dict_type',
]

T = TypeVar('T')


def literal_value_type(arg: str):
    if arg.upper() == 'TRUE':
        return True
    elif arg.upper() == 'FALSE':
        return False
    try:
        return int(arg)
    except ValueError:
        try:
            return float(arg)
        except ValueError:
            pass

    return arg


def literal_str_type(constant: tuple[str, ...]) -> Callable[[str], str]:
    def _type(arg: str):
        if arg in constant:
            return arg

        found = [it for it in constant if it.startswith(arg)]
        if len(found) == 1:
            return found[0]
        elif len(found) == 0:
            raise ValueError(f'unknown "{arg}". should one of {str(constant)}')
        else:
            raise ValueError(f'conflict "{arg}" between {str(found)}')

    return _type


def union_type(union_type_args):
    """union type `Union[T1, T2]` caster.

    :param union_type_args: union type arguments. (T1, T2)
    :return: type caster
    """
    none_type = type(None)

    def _type(value: str):
        for _a in union_type_args:
            if _a is not none_type:
                try:
                    return _a(value)
                except (TypeError, ValueError):
                    pass
        raise ValueError

    return _type


def bool_type(value: str) -> bool:
    value = value.lower()
    if value in ('-', '0', 'f', 'false', 'n', 'no', 'x'):
        return False
    elif value in ('', '+', '1', 't', 'true', 'yes', 'y'):
        return True
    else:
        raise ValueError()


def ann_type(a_name: str, a_type):
    """annotation type caster.

    :param a_name: annotation name.
    :param a_type: annotation type.
    :return: type caster.
    """
    a_type_ori = get_origin(a_type)
    if a_type == Any:
        return None
    if a_type_ori == Literal:
        return literal_str_type(get_args(a_type))
    elif a_type_ori == Union:
        return union_type(get_args(a_type))
    elif a_type_ori is not None and (callable(a_type_ori) or isinstance(a_type_ori, type)):
        return a_type_ori
    elif callable(a_type) or isinstance(a_type, type):
        return a_type
    else:
        raise RuntimeError(f'{a_name} {a_type}')


@overload
def tuple_type(value_type: Callable[[str], T] = str, n: int = None, *, split=','):
    pass


@overload
def tuple_type(value_type: tuple = str, *, split=','):
    pass


def tuple_type(value_type=str, n: int = None, *, split=','):
    if n is None:
        if isinstance(value_type, tuple):
            n = len(value_type)

    if n is not None and n <= 0:
        raise ValueError()
    elif n is None:
        n = 0  # no-limited

    def _cast(arg: str) -> tuple[T, ...]:
        if callable(value_type):
            return tuple(map(value_type, arg.split(split, maxsplit=(n - 1))))
        else:
            return tuple(map(lambda it: it[0](it[1]), zip(value_type, arg.split(split, maxsplit=(n - 1)))))

    return _cast


def list_type(value_type: Callable[[str], T] = str, *, split=',', prepend: list[T] = None):
    """:attr:`arg.type` caster which convert comma ',' spread string into list.

    :param split: split character
    :param value_type: value type converter
    :param prepend: prepend list
    :return: type caster.
    """

    def _cast(arg: str) -> list[T]:
        value = list(map(value_type, arg.split(split)))

        if arg.startswith('+') and prepend is not None:
            return [*prepend, *value]
        else:
            return list(value)

    return _cast


def dict_type(value_type: Callable[[str], T] | dict[str, type | Callable[[str], T]] = str, *,
              entry_sep: str = ',',
              kv_sep: str = '=',
              quote: str = '"',
              prepend: dict[str, T] = None):
    """Dict arg value.

    :param value_type: type of dict value
    :param entry_sep: single character as entry seperator
    :param kv_sep: single character candidates as key-value seperator
    :param prepend: default dict content
    :return: type converter
    """
    if prepend is None:
        prepend = {}

    def _type(arg: str) -> dict[str, T]:
        ret = dict(prepend)

        while len(arg):
            k, v, arg = _dict_value(arg, entry_sep, kv_sep, quote)
            if callable(value_type):
                v = value_type(v)
            else:
                try:
                    vf = value_type[k]
                except KeyError:
                    try:
                        vf = value_type[...]
                    except KeyError:
                        vf = str

                v = vf(v)
            ret[k] = v

        return ret

    return _type


def _dict_value(expr: str,
                entry_sep: str = ',',
                kv_sep: str = '=',
                quote: str = '"') -> tuple[str, str, str]:
    x = len(expr)
    e = e if (e := expr.find(entry_sep)) >= 0 else x
    k = k if (k := expr.find(kv_sep)) >= 0 else x
    if k == e == x:
        if x == 0:
            return "", "", ""
        else:
            return expr, "", ""
    elif k < e:  # KEY=...
        r1 = expr[:k]
        r2 = expr[k + 1:]
        if len(r2) == 0:  # KEY=
            return r1, "", ""
        elif r2.startswith(quote):  # KEY="...
            if (q := r2.find(quote, 1)) < 0:
                raise ValueError(f'missing "{quote}" @ {r2}')
            r3 = r2[q + 1:]
            r2 = r2[1:q]
            return r1, r2, r3
        else:
            r2 = expr[k + 1:e]
            r3 = expr[e + 1:]
            return r1, r2, r3
    else:  # e < k # KEY,...
        r1 = expr[:e]
        r3 = expr[e + 1:]
        return r1, "", r3
