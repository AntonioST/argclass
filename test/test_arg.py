import unittest

from argclass import arg
from argclass.core import foreach_arguments, with_defaults


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

if __name__ == '__main__':
    unittest.main()
