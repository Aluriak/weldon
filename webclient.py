
import socket
import base64
import inspect

import wjson
from server import Server
from commons import ServerError
from webserver import PORT as TCP_PORT, BUFFER_SIZE
from hybrid_encryption import HybridEncryption


TCP_IP = '127.0.0.1'


def create_payload(function:str, *args:str, keypair=None, server_pubkey=None, **kwargs) -> bytes:
    """Create and return the payload.

    Will encrypt it if keypair and server public key are given.

    """
    print('COMMAND:', function)
    payload = wjson.as_json((function, tuple(args), dict(kwargs)))
    print('RAW PAYLOAD:', payload)
    key = None
    if keypair and server_pubkey:
        payload, key = keypair.encrypt(payload, server_pubkey)
        payload = base64.b64encode(payload).decode()  # convert binary into str
        key = base64.b64encode(key).decode()
    assert isinstance(key, str) or key is None
    assert isinstance(payload, str)
    data = wjson.as_json({
        'encryption_key': key,
        'payload': payload,
    })
    print('READY PAYLOAD:', data)
    print('ENCODED PAYLOAD:', data.encode())
    return data.encode()


def send(payload:bytes, port:int=TCP_PORT, buffer_size:int=BUFFER_SIZE,
         host:str=TCP_IP) -> bytes:
    """Send and retrieve the answer through TCP socket"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print('PAYLOAD TO SEND:', payload)
    s.send(payload)

    buffer = True
    received = ''
    while buffer:
        buffer = s.recv(buffer_size).decode()
        received += buffer
    print('RECEIVED:', received)
    data = wjson.from_json(received)
    s.close()
    return data


def extract_payload(data:dict, keypair=None) -> str:
    """Return the (decrypted) payload found in data, or raise a ServerError
    when failed status"""
    assert data['status'] in {'failed', 'succeed'}, 'status is not failed nor succeed'
    if data['status'] == 'failed':
        raise ServerError(data['payload'])
    elif data['encryption_key']:  # success & encrypted
        payload = base64.b64decode(data['payload'])
        key = base64.b64decode(data['encryption_key'])
        if not keypair:
            raise ValueError("Payload is encrypted, but keypair is not provided")
        print('SVFJGL RECEIVED KEY:', data['encryption_key'])
        print('SVFJGL PUBKEY:', key)
        ret = keypair.decrypt(payload, key)
    else:  # succeed but not encrypted
        ret = data['payload']
    print('RECEIVED PAYLOAD:', ret)
    return ret


class Send:
    """Wrapper around send function, allowing user to specify only once
    some parameters (notabily token and problem).

    This object adapt itself to available Server API by asking the server
    directly about available API, so only the api access and the registration
    needs to be common.

    Consequently, this object do not need the Server source code,
    and also natively manage rooters access to their specific API.

    """

    def __init__(self, registration_password:str, name:str, problem=None,
                 root:bool=False, port:int=TCP_PORT,
                 buffer_size:int=BUFFER_SIZE, host:str=TCP_IP,
                 keypair:HybridEncryption=None):
        self.token = None
        self.problem_id = problem
        self.port = int(port)
        self.buffer_size = int(buffer_size)
        self.host = str(host)
        self.root = bool(root)
        self.name = str(name)
        self.keypair = keypair
        self.registration_password = str(registration_password)
        self.known_params = {'token', 'problem', 'problem_id'}
        self.get_server_pubkey()
        self.register()
        self.implement_api()

    def get_server_pubkey(self):
        """Contact the server in order to get its public key"""
        self.server_pubkey = None
        self.server_pubkey = self._send(command='get_public_key')
        print('SERVER PUBLIC KEY:', self.server_pubkey)


    def register(self):
        """Perform the registration on the server"""
        register = 'register_rooter' if self.root else 'register_player'
        self.token = self._send(
            command=register,
            name=self.name,
            password=self.registration_password,
            public_key=self.keypair.publickey_as_string if self.keypair else None,
        )


    def implement_api(self):
        """Will ask the server about available API.
        Will dynamically create the methods for self with the parameters
        that are not deductible from already known information (notabily token).

        This method uses black magic.
        See https://stackoverflow.com/a/2982/3077939 for details.

        """
        self.server_api = self._send('get_api', token=self.token)
        # generate all functions according to received api
        for name, params in self.server_api.items():
            if any(not param.isidentifier() for param in params):
                raise ValueError("Server sent API method parameter that is not "
                                 "a valid identifier: " + ', '.join(params))
            method_name = name
            method_params = tuple(param for param in params if param not in self.known_params)
            known_params = tuple(param for param in params if param in self.known_params)
            # generate the method definition
            method_def = "def {}(self, {} **kwargs):\n return self._send('{}', {}{}{})".format(
                method_name, ', '.join(method_params) + ',' if method_params else '',
                method_name,
                ', '.join('{p}=kwargs.get("{p}", self.{p})'.format(p=param) for param in known_params),
                ', ' if known_params else '',
                ', '.join('{p}={p}'.format(p=param) for param in method_params),
            )
            # run the code, then __get__ the bounded-to-self version
            #  of the function, and put it as an attribute of self.
            exec(method_def)
            setattr(self, method_name, locals()[method_name].__get__(self))


    def _send(self, command, **kwargs):
        """Send request to the server"""
        payload = create_payload(command, **kwargs,
                                 keypair=self.keypair,
                                 server_pubkey=self.server_pubkey)
        return wjson.from_json(extract_payload(send(
            payload, port=self.port,
            buffer_size=self.buffer_size, host=self.host
        ), keypair=self.keypair))
