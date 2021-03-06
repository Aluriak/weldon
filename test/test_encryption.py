

import encryption as enc
import hybrid_encryption as henc


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


def test_aes_cipher():
    cipher = henc.AESCipher(b'hadoken!hadoken!')
    assert cipher.decrypt(cipher.encrypt('coucou')) == 'coucou'

def test_aes_cipher_with_lots_of_data():
    cipher = henc.AESCipher(b'hadoken!hadoken!')
    data = 'coucou'*1000000
    assert cipher.decrypt(cipher.encrypt(data)) == data


def test_hybrid_encryption():
    cipher = henc.HybridEncryption()
    assert cipher.decrypt(*cipher.encrypt('coucou', cipher.publickey)) == 'coucou'


def test_hybrid_encryption_two_agents():
    # Let's retry the same thing, but with distinct keypairs
    # Alice and Bob have their personnal key pair
    alice = henc.HybridEncryption()
    bob = henc.HybridEncryption()

    # Bob send a message to Alice using her public key.
    message = bob.encrypt('Hi Alice !', alice.publickey)
    assert message != 'Hi Alice !'

    # Alice decrypt the message (a pair (data, key)) using its key pair.
    alice_received = alice.decrypt(*message)
    assert alice_received == 'Hi Alice !'


def test_hybrid_pubkey_export():
    cipher = henc.HybridEncryption()
    assert isinstance(cipher.publickey, bytes)
    assert isinstance(cipher.publickey_as_bytes, bytes)
    assert isinstance(cipher.publickey_as_string, str)
    assert isinstance(cipher.publickey_as_b64, str)
    assert not isinstance(cipher.publickey_as_obj, (bytes, str))

    recovered = henc.HybridEncryption.publickey_from(cipher.publickey_as_bytes)
    assert recovered == cipher.publickey_as_obj

    recovered = henc.HybridEncryption.publickey_from(cipher.publickey_as_string)
    assert recovered == cipher.publickey_as_obj

    recovered = henc.HybridEncryption.publickey_from_b64(cipher.publickey_as_b64)
    assert recovered == cipher.publickey_as_obj
