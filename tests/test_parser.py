import unittest

from argclass import AbstractOptions, arg


class C(AbstractOptions):
    a: int = arg('-a')
    b: int = arg('-b', default=0)

    def run(self):
        pass


class TestParser(unittest.TestCase):
    def test_main_exit(self):
        with self.assertRaises(SystemExit) as e:
            C().main([])

        self.assertEqual(0, e.exception.code)

    def test_main_exit_parsing_error(self):
        with self.assertRaises(SystemExit) as e:
            C().main(['-e'])

        self.assertEqual(2, e.exception.code)

    def test_main_exit_run_error(self):
        class D(C):
            def run(self):
                return 10

        with self.assertRaises(SystemExit) as e:
            D().main(['-a=1'])

        self.assertEqual(10, e.exception.code)

    def test_init_copy(self):
        c = C()
        c.main(['-a=10', '-b=10'], system_exit=False)
        self.assertEqual(10, c.a)
        self.assertEqual(10, c.b)

        d = C(c)
        self.assertEqual(10, d.a)
        self.assertEqual(10, d.b)

    def test_usage(self):
        class C(AbstractOptions):
            @classmethod
            def parser_usage(cls):
                return "%(prog)s test"

            def run(self):
                pass

        self.assertEqual(C.print_usage(prog='TEST'), """\
usage: TEST test
""")
        self.assertEqual(C.print_help(prog='TEST'), """\
usage: TEST test

options:
  -h, --help  show this help message and exit
""")

    def test_epilog(self):
        class C(AbstractOptions):
            @classmethod
            def parser_epilog(cls):
                return "test"

            def run(self):
                pass

        self.assertEqual(C.print_help(prog='TEST'), """\
usage: TEST [-h]

options:
  -h, --help  show this help message and exit

test
""")


if __name__ == '__main__':
    unittest.main()
