"""encapsulation of pycrypto module.

If the module is not available, will fall back on no-encryption.

"""

try:
    import Crypto
    from Crypto.PublicKey import RSA
    from Crypto import Random
    from Crypto.Hash import MD5
except ImportError:
    print('Cryptography is not available. Communications with server '
          'are not protected against sniffing.')
    Crypto = None


KEY_LENGTH = 1024 * 4  # in bits
random_gen = Random.new().read if Crypto else None


def generate_key_pair():
    """Return a key pair"""
    return RSA.generate(KEY_LENGTH, random_gen) if Crypto else None

def encrypt(data:bytes, public_key) -> bytes:
    """Return given data, encrypted using public key"""
    if Crypto and public_key is not None:
        help(public_key.encrypt)
        return public_key.encrypt(data, int.from_bytes(random_gen(4), 'big'))
    return data

def decrypt(data:bytes, keypair) -> bytes:
    """Return given data, decrypted using private key"""
    if Crypto and keypair is not None:
        return keypair.decrypt(data)
    return data

def public_key_from_key_pair(keypair):
    if Crypto and keypair is not None:
        return keypair.publickey()
    return None

