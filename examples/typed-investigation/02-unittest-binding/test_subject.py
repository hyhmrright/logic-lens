import unittest as u
from subject import attach as f
class Binding(u.TestCase):
    def test_default(self):
        self.assertEqual(f(b'A'), b'A!')
    def test_keyword(self):
        self.assertEqual(f(b'A', enabled=False), b'A')
