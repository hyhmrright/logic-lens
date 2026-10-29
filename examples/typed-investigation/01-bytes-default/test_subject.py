from subject import attach
class TestAttach:
    def test_bytes(self):
        data=b'A'
        assert attach(data) == b'A!'
