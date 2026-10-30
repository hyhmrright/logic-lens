from subject import attach
def test_a():
    assert attach(b'A') == b'A!'
def test_b():
    assert attach(b'A', suffix=b'!') == b'wrong'
