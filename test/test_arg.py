import unittest
from typing import List

from argclass import arg, list_type
from argclass.core import foreach_arguments, with_defaults, AbstractOptions


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
        self.assertEquals(3, len(args))
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
        self.assertEquals(3, len(args))
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

        self.assertEquals(3, len(args))
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

        self.assertEquals(2, len(args))
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
        self.assertEquals(c.c, 'c')


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

    def test_int_defaults(self):
        class C:
            a: int = arg('-a')
            b: int = arg('-b', default=0)

        c = with_defaults(C())
        with self.assertRaises(AttributeError):
            c.a
        self.assertEquals(0, c.b)

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
        self.assertEquals(0, c.b)

    def test_parse_bool(self):
        class C(AbstractOptions):
            a: bool = arg('-a')

            def run(self):
                pass

        c = C()
        c.main([], parse_only=True)
        self.assertFalse(c.a)
        c.main(['-a'], parse_only=True)
        self.assertTrue(c.a)

    def test_parse_int(self):
        class C(AbstractOptions):
            a: int = arg('-a')

            def run(self):
                pass

        c = C()
        c.main([], parse_only=True)
        self.assertIsNone(c.a)

        c.main(['-a', '1'], parse_only=True)
        self.assertEquals(1, c.a)

    def test_parse_list(self):
        class C(AbstractOptions):
            a: List[int] = arg('-a', type=list_type(int))

            def run(self):
                pass

        c = C()
        c.main([], parse_only=True)
        self.assertIsNone(c.a)

        c.main(['-a', '1'], parse_only=True)
        self.assertListEqual([1], c.a)

        c.main(['-a', '1,2,3'], parse_only=True)
        self.assertListEqual([1, 2, 3], c.a)


if __name__ == '__main__':
    unittest.main()
