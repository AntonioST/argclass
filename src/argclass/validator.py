from collections.abc import Callable
from typing import TypeVar, get_origin, Any, Literal, get_args, Union

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


def tuple_type(value_type: Union[Callable[[str], T], tuple] = str, n: int = None, split=','):
    if n is None:
        if isinstance(value_type, tuple):
            n = len(value_type)

    if n is not None and n <= 0:
        raise ValueError()
    elif n is None:
        n = 0  # no-limited

    def _cast(arg: str) -> tuple[T, ...]:
        if isinstance(value_type, tuple):
            return tuple(map(lambda it: it[0](it[1]), zip(value_type, arg.split(split, maxsplit=(n - 1)))))
        else:
            return tuple(map(value_type, arg.split(split, maxsplit=(n - 1))))

    return _cast


def list_type(value_type: Callable[[str], T] = str, split=',', prepend: tuple[T, ...] = None):
    """:attr:`arg.type` caster which convert comma ',' spread string into list.

    :param split: split character
    :param value_type: value type converter
    :param prepend: prepend list
    :return: type caster.
    """

    def _cast(arg: str) -> tuple[T, ...]:
        value = list(map(value_type, arg.split(split)))

        if arg.startswith('+') and prepend is not None:
            return tuple(*prepend, *value)
        else:
            return tuple(value)

    return _cast


def dict_type(default: dict[str, T] = None,
              value_type: Callable[[str], T] = str,
              entry_sep: str = ',',
              kv_sep: str = '='):
    """Dict arg value.

    :param default: default dict content
    :param value_type: type of dict value
    :param entry_sep: single character as entry seperator
    :param kv_sep: single character candidates as key-value seperator
    :return: type converter
    """
    if default is None:
        default = {}

    def _type(arg: str) -> dict[str, T]:
        ret = dict(default)

        for value in arg.split(entry_sep):
            for sep in kv_sep:
                if sep in value:
                    k, _, v = value.partition(sep)
                    if value_type is not None:
                        v = value_type(v)
                    ret[k] = v
                    break
            else:
                if value_type is not None:
                    default[value] = value_type("")
                else:
                    default[value] = None

        return ret

    return _type
