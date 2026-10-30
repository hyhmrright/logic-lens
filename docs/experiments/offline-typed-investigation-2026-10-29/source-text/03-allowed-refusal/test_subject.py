from unittest import TestCase as Case
from subject import check
class Refusal(Case):
    def test_refusal(self):
        with self.assertRaises(ValueError):
            check(b'AAAA')
