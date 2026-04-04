from connect4.api.passwords import hash_password, verify_password


def test_hash_and_verify_success():
    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed)


def test_verify_wrong_password():
    hashed = hash_password("mysecretpassword")
    assert not verify_password("wrongpassword", hashed)


def test_hash_produces_different_hashes():
    h1 = hash_password("samepassword")
    h2 = hash_password("samepassword")
    assert h1 != h2
