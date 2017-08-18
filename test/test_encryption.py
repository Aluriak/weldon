

import encryption as enc


def test_all():
    run()


def test_without_module():
    real_crypto = enc.Crypto
    enc.Crypto = None
    run(crypto=False)
    enc.Crypto = real_crypto


def run(crypto:bool=True):
    MESSAGE = 'This is a payload to be encrypted'
    pair = enc.generate_key_pair()
    encrypted = enc.encrypt(MESSAGE.encode(), enc.public_key_from_key_pair(pair))
    decrypted = enc.decrypt(encrypted, pair)
    assert decrypted.decode() == MESSAGE

    if not crypto:
        assert encrypted == MESSAGE.encode()
        assert enc.Crypto is None
        assert enc.public_key_from_key_pair(pair) is None
    else:  # crypto is available
        assert encrypted != MESSAGE.encode()
        assert enc.Crypto is not None
        assert enc.public_key_from_key_pair(pair) is not None
