import unittest
from unittest.main import main

def get_sum(main):

    return main + "ALL OK"

class TestSum(unittest.TestCase):
    def test_get_sum(self):
        self.assertEqual(get_sum(main))
if __name__ == '__main_':
    unittest.main()
