"""encapsulation of pycrypto module.

If the module is not available, will fall back on no-encryption.

"""

try:
    import Crypto
    from Crypto.Cipher import PKCS1_OAEP
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
    return RSA.generate(KEY_LENGTH, e=65537) if Crypto else None

def encrypt(data:bytes, public_key) -> bytes:
    """Return given data, encrypted using public key"""
    if Crypto and public_key is not None:
        cipher = PKCS1_OAEP.new(RSA.importKey(public_key.exportKey("DER")))
        return cipher.encrypt(data)
    return data

def decrypt(data:bytes, keypair) -> bytes:
    """Return given data, decrypted using private key"""
    if Crypto and keypair is not None:
        key = RSA.importKey(keypair.exportKey("DER"))
        cipher = PKCS1_OAEP.new(key)
        return cipher.decrypt(data)
    return data

def public_key_from_key_pair(keypair):
    if Crypto and keypair is not None:
        return keypair.publickey()
    return None
