import front as api
class TestAPI:
    def test_attach(self):
        assert api.public(b'A', suffix=b'?') == b'A?'
