import unittest

from argclass.validator import _dict_value


class DictTypeTest(unittest.TestCase):
    def test_dict_value(self):
        self.assertEqual(("", "", ""), _dict_value(""))
        self.assertEqual(("1", "", ""), _dict_value("1"))
        self.assertEqual(("1", "", "2"), _dict_value("1,2"))
        self.assertEqual(("1", "", "2,3"), _dict_value("1,2,3"))
        self.assertEqual(("1", "a", ""), _dict_value("1=a"))
        self.assertEqual(("1", "a", "2=b"), _dict_value("1=a,2=b"))
        self.assertEqual(("1", "", ""), _dict_value("1="))
        self.assertEqual(("1", "", "2=b"), _dict_value("1=,2=b"))


if __name__ == '__main__':
    unittest.main()
