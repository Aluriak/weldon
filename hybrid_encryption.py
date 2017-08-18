"""Implementation of hybrid encryption
with a very simple API.

"""
import base64
from Crypto import Random
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA


KEY_LENGTH = 1024 * 2
random_gen = Random.new().read


class AESCipher(object):

    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = random_gen(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    @staticmethod
    def _pad(s, bs:int=AES.block_size):
        return s + (bs - len(s) % bs) * chr(bs - len(s) % bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]


class HybridEncryption:
    """Naive implementation of an hybrid encryption.

    Encryption output (and decryption input) is a pair (data, key),
    where data is the (AES-encrypted) payload to transmit securely,
    and key is the (RSA-encrypted) AES key.

    If none is given at instanciation, an RSA keypair will be generated
    and used.

    >>> cipher = HybridEncryption()
    >>> cipher.decrypt(*cipher.encrypt('coucou', cipher.publickey))
    'coucou'

    """

    def __init__(self, keypair=None, aes_key_size:int=32, rsa_key_size:int=1024*2):
        self._keypair = keypair or RSA.generate(rsa_key_size, e=65537)
        self._privkey = self._keypair.exportKey('DER')
        self._aes_key_size = int(aes_key_size)


    def encrypt(self, data:bytes, pubkey) -> (bytes, bytes):
        """Return given data as a 2-uplet (encrypted data, key).

        key is encrypted using given RSA public key.

        """
        aes_key = random_gen(self._aes_key_size)
        encrypted_data = AESCipher(aes_key).encrypt(data)
        return encrypted_data, self._encrypted_aes_key(aes_key, pubkey)

    def decrypt(self, data:bytes, key:bytes) -> bytes:
        """Return decrypted data. Key is assumed encrypted using
        self's public key"""
        aes_key = self._decrypted_aes_key(key)
        return AESCipher(aes_key).decrypt(data)


    def _encrypted_aes_key(self, aes_key:bytes, pubkey) -> bytes:
        """Use RSA keypair in order to encrypt given aes key"""
        cipher = PKCS1_OAEP.new(RSA.importKey(pubkey.exportKey('DER')))
        return cipher.encrypt(aes_key)

    def _decrypted_aes_key(self, enc_aes_key:bytes) -> bytes:
        """Use RSA private key in order to decrypt given aes key."""
        cipher = PKCS1_OAEP.new(RSA.importKey(self._keypair.exportKey('DER')))
        return cipher.decrypt(enc_aes_key)

    @property
    def publickey(self): return self._keypair.publickey()


if __name__ == '__main__':
    cipher = AESCipher(b'hadoken!hadoken!')
    assert cipher.decrypt(cipher.encrypt('coucou')) == 'coucou'

    cipher = HybridEncryption()
    assert cipher.decrypt(*cipher.encrypt('coucou', cipher.publickey)) == 'coucou'

    # Let's retry the same thing, but with distinct keypairs
    # Alice and Bob have their personnal key pair
    alice = HybridEncryption()
    bob = HybridEncryption()

    # Bob send a message to Alice using her public key.
    message = bob.encrypt('Hi Alice !', alice.publickey)

    # Alice decrypt the message (a pair (data, key)) using its key pair.
    alice_received = alice.decrypt(*message)
    assert alice_received == 'Hi Alice !'
