import unittest
from typing import Any, Literal

from argclass import arg, list_type, dict_type, tuple_type, as_arg, posarg, vararg
from argclass.core import foreach_arguments, with_defaults, AbstractOptions, missing


class TestField(unittest.TestCase):
    def test_foreach_arguments(self):
        class C:
            a: str = arg('-a')
            b: str = arg('-b')
            c: str = arg('-c')

        args = {
            it.options[0]: it
            for it in foreach_arguments(C)
        }
        self.assertEqual(3, len(args))
        self.assertIn('-a', args)
        self.assertIn('-b', args)
        self.assertIn('-c', args)
        self.assertIs(args['-a'], C.a)
        self.assertIs(args['-b'], C.b)
        self.assertIs(args['-c'], C.c)

    def test_foreach_arguments_inherit(self):
        class A:
            a: str = arg('-a')

        class B(A):
            b: str = arg('-b')

        class C(B):
            c: str = arg('-c')

        args = {
            it.options[0]: it
            for it in foreach_arguments(C)
        }
        self.assertEqual(3, len(args))
        self.assertIn('-a', args)
        self.assertIn('-b', args)
        self.assertIn('-c', args)
        self.assertIs(args['-a'], C.a)
        self.assertIs(args['-b'], C.b)
        self.assertIs(args['-c'], C.c)

    def test_foreach_arguments_inherit_h(self):
        class A:
            a: str = arg('-a')

        class B:
            b: str = arg('-b')

        class C(A, B):
            c: str = arg('-c')

        args = {
            it.options[0]: it
            for it in foreach_arguments(C)
        }

        self.assertEqual(3, len(args))
        self.assertIn('-a', args)
        self.assertIn('-b', args)
        self.assertIn('-c', args)
        self.assertIs(args['-a'], C.a)
        self.assertIs(args['-b'], C.b)
        self.assertIs(args['-c'], C.c)

    def test_foreach_arguments_inherit_overwrite(self):
        class A:
            a: str = arg('-a')

        class B:
            b: str = arg('-b')

        class C(A, B):
            c: str = arg('-c')
            a: str = 'a'

        args = {
            it.options[0]: it
            for it in foreach_arguments(C)
        }

        self.assertEqual(2, len(args))
        self.assertNotIn('-a', args)
        self.assertIn('-b', args)
        self.assertIn('-c', args)
        self.assertIs(args['-b'], C.b)
        self.assertIs(args['-c'], C.c)

    def test_with_defaults(self):
        class C:
            a: str = arg('-a')
            b: str = arg('-b', default=None)
            c: str = arg('-c', default='c')

        c = with_defaults(C())

        with self.assertRaises(AttributeError):
            c.a

        self.assertIsNone(c.b)
        self.assertEqual(c.c, 'c')


class TestArgField(unittest.TestCase):

    def test_bool(self):
        class C:
            a: bool = arg('-a')
            b: bool = arg('-b', action='store_true')
            c: bool = arg('-c', action='store_false')

        self.assertFalse(C.a.default)
        self.assertFalse(C.b.default)
        self.assertTrue(C.c.default)

    def test_non_bool(self):
        class C:
            a: str = arg('-a')
            b: int = arg('-b')

        self.assertIs(missing, C.a.default)
        self.assertIs(missing, C.b.default)

    def test_cast_bool(self):
        class C:
            a: bool = arg('-a')

        self.assertTrue(C.a.cast('True'))
        self.assertFalse(C.a.cast('False'))

    def test_cast_int(self):
        class C:
            a: int = arg('-a')

        self.assertEqual(0, C.a.cast('0'))
        self.assertEqual(1, C.a.cast('1'))
        with self.assertRaises(ValueError):
            C.a.cast('a')

    def test_cast_with_validator(self):
        class C:
            a: int = arg('-a', validator=lambda it: it >= 0)

        self.assertEqual(0, C.a.cast('0'))
        self.assertEqual(1, C.a.cast('1'))
        with self.assertRaises(ValueError) as capture:
            C.a.cast('-1')
        self.assertEqual('-1', capture.exception.args[0])


class TestArgType(unittest.TestCase):
    def test_bool_defaults(self):
        class C:
            a: bool = arg('-a')
            b: bool = arg('-b', action='store_true')
            c: bool = arg('-c', action='store_false')

        c = with_defaults(C())
        self.assertFalse(c.a)
        self.assertFalse(c.b)
        self.assertTrue(c.c)

    def test_bool_constant(self):
        class C:
            a: bool = arg('-a')
            b: bool = arg('-b', action='store_true')
            c: bool = arg('-c', action='store_false')

        self.assertTrue(as_arg(C.a).const)
        self.assertTrue(as_arg(C.b).const)
        self.assertFalse(as_arg(C.c).const)

    def test_int_defaults(self):
        class C:
            a: int = arg('-a')
            b: int = arg('-b', default=0)

        c = with_defaults(C())
        with self.assertRaises(AttributeError):
            c.a
        self.assertEqual(0, c.b)

    def test_int_constant(self):
        class C:
            a: int = arg('-a')
            b: int = arg('-b', const=10)

        self.assertIs(missing, as_arg(C.a).const)
        self.assertEqual(10, as_arg(C.b).const)

    def test_bool_parser_defaults(self):
        class C(AbstractOptions):
            a: bool = arg('-a')
            b: bool = arg('-b', action='store_true')
            c: bool = arg('-c', action='store_false')

            def run(self):
                pass

        c = C()
        self.assertFalse(c.a)
        self.assertFalse(c.b)
        self.assertTrue(c.c)

    def test_int_parser_defaults(self):
        class C(AbstractOptions):
            a: int = arg('-a')
            b: int = arg('-b', default=0)

            def run(self):
                pass

        c = C()
        with self.assertRaises(AttributeError):
            c.a
        self.assertEqual(0, c.b)

    def test_parse_bool(self):
        class C(AbstractOptions):
            a: bool = arg('-a')

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertFalse(c.a)
        self.assertEqual(0, c.main(['-a'], parse_only=True))
        self.assertTrue(c.a)

    def test_parse_int(self):
        class C(AbstractOptions):
            a: int = arg('-a')

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-a', '1'], parse_only=True))
        self.assertEqual(1, c.a)

    def test_multiple_args(self):
        class C(AbstractOptions):
            a: int = arg('-a', default=0)

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertEqual(0, c.a)
        self.assertEqual(0, c.main(['-a1', '-a2'], parse_only=True))
        self.assertEqual(2, c.a)

    def test_parse_literal(self):
        class C(AbstractOptions):
            a: Literal['A', 'B'] = arg('-a')

            def run(self):
                pass

        c = C()
        self.assertEqual(('A', 'B'), as_arg(C.a).choices)
        self.assertEqual(0, c.main(['-a=A'], parse_only=True))
        self.assertEqual('A', c.a)

        self.assertEqual(2, c.main(['-a=C'], parse_only=True))

    def test_set_default(self):
        class C(AbstractOptions):
            a: int = arg('-a').set_default(None, 0)
            b: int = arg('-b', default=0)

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        c = C()
        self.assertEqual(0, c.main(['-a'], parse_only=True))
        self.assertEqual(0, c.a)

        c = C()
        self.assertEqual(0, c.main(['-a=10'], parse_only=True))
        self.assertEqual(10, c.a)

        c = C()
        self.assertEqual(0, c.main(['-a', '10'], parse_only=True))
        self.assertEqual(10, c.a)

    def test_with_options(self):
        class C(AbstractOptions):
            a: int = arg('-a', default=0)

            def run(self):
                pass

        class D(C):
            a: int = as_arg(C.a).with_options(default=10)

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertEqual(0, c.a)

        c = D()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertEqual(10, c.a)

class TestListArgType(unittest.TestCase):
    def test_parse_list(self):
        class C(AbstractOptions):
            a: list[int] = arg('-a', type=list_type(int))

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-a', '1'], parse_only=True))
        self.assertListEqual([1], c.a)

        self.assertEqual(0, c.main(['-a', '1,2,3'], parse_only=True))
        self.assertListEqual([1, 2, 3], c.a)


class TestTupleArgType(unittest.TestCase):
    def test_parse_tuple(self):
        class C(AbstractOptions):
            a: tuple[int, ...] = arg('-a', type=tuple_type(int))

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-a', '1'], parse_only=True))
        self.assertEqual((1,), c.a)

        self.assertEqual(0, c.main(['-a', '1,2,3'], parse_only=True))
        self.assertEqual((1, 2, 3), c.a)

    def test_parse_tuple_fix_length(self):
        class C(AbstractOptions):
            a: tuple[int, int] = arg('-a', type=tuple_type(int, n=2))

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-a', '1,2'], parse_only=True))
        self.assertEqual((1, 2), c.a)

        self.assertNotEqual(0, c.main(['-a', '1,2,3'], parse_only=True))

    def test_parse_tuple_var_type(self):
        class C(AbstractOptions):
            a: tuple[int, float, str] = arg('-a', type=tuple_type((int, float, str)))

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-a', '1,2,c'], parse_only=True))
        self.assertEqual((1, 2.0, 'c'), c.a)

        self.assertNotEqual(0, c.main(['-a', 'c,2,3'], parse_only=True))

    @unittest.skip('not support infer tuple type from annotations')
    def test_parse_tuple_ann_int_type(self):
        class C(AbstractOptions):
            a: tuple[int, ...] = arg('-a')

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-a', '1,2,3'], parse_only=True))
        self.assertEqual((1, 2, 3), c.a)

    @unittest.skip('not support infer tuple type from annotations')
    def test_parse_tuple_ann_var_type(self):
        class C(AbstractOptions):
            a: tuple[int, float, str] = arg('-a')

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-a', '1,2,c'], parse_only=True))
        self.assertEqual((1, 2.0, 'c'), c.a)

        self.assertNotEqual(0, c.main(['-a', 'c,2,3'], parse_only=True))


class TestDictArgType(unittest.TestCase):
    def test_parse_dict(self):
        class C(AbstractOptions):
            a: dict[str, int] = arg('-a', type=dict_type(int))

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-aA=1'], parse_only=True))
        self.assertDictEqual({'A': 1}, c.a)

        self.assertEqual(0, c.main(['-aA=1,B=2'], parse_only=True))
        self.assertDictEqual({'A': 1, 'B': 2}, c.a)

    def test_parse_dict_cast(self):
        class C(AbstractOptions):
            a: dict[str, Any] = arg('-a', type=dict_type({
                'int': int,
                'str': str,
                'float': float
            }))

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-aint=1,float=2.1,str=c,other=d'], parse_only=True))
        self.assertDictEqual({'int': 1, 'float': 2.1, 'str': 'c', 'other': 'd'}, c.a)

    def test_parse_dict_cast_default(self):
        class C(AbstractOptions):
            a: dict[str, Any] = arg('-a', type=dict_type({
                'int': int,
                'str': str,
                'float': float,
                ...: lambda it: 'invalid'
            }))

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main([], parse_only=True))
        self.assertIsNone(c.a)

        self.assertEqual(0, c.main(['-aint=1,float=2.1,str=c,other=d'], parse_only=True))
        self.assertDictEqual({'int': 1, 'float': 2.1, 'str': 'c', 'other': 'invalid'}, c.a)


class TestPosArgType(unittest.TestCase):
    def test_pos_arg(self):
        class C(AbstractOptions):
            a: str = posarg('A')

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main(['10'], parse_only=True))
        self.assertEqual('10', c.a)

    def test_multiple_pos_arg(self):
        class C(AbstractOptions):
            a: str = posarg('A')
            b: int = posarg('B')
            c: float = posarg('C')

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main(['10', '11', '12'], parse_only=True))
        self.assertEqual('10', c.a)
        self.assertEqual(11, c.b)
        self.assertEqual(12, c.c)

    def test_var_pos_arg(self):
        class C(AbstractOptions):
            a: list[str] = vararg('A')

            def run(self):
                pass

        c = C()
        self.assertEqual(0, c.main(['10', '11', '12'], parse_only=True))
        self.assertListEqual(['10', '11', '12'], c.a)


if __name__ == '__main__':
    unittest.main()
