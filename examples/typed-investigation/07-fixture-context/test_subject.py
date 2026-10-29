from unittest import TestCase
from subject import attach
class TestState(TestCase):
    def setUp(self):
        self.data=b'A'
    def test_state(self):
        self.assertEqual(attach(b'A'), b'A')
