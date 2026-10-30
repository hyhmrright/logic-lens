from subject import classify
class TestContent:
    def test_a(self):
        assert classify(b'A') == 1
    def test_b(self):
        assert classify(b'B') == 2
