
import socket
import inspect

import wjson
from server import Server
from webserver import PORT as TCP_PORT, BUFFER_SIZE


TCP_IP = '127.0.0.1'

def __faild_on(payload):
    """Default failure handler when received data is in fail state"""
    print('ServerError:', payload)
    exit(1)

def send(function:str, *args:str, port:int=TCP_PORT,
         buffer_size:int=BUFFER_SIZE, host:str=TCP_IP,
         failed_on=__faild_on, **kwargs):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    payload = wjson.as_json((function, tuple(args), dict(kwargs))).encode()
    s.send(payload)

    buffer = True
    received = ''
    while buffer:
        buffer = s.recv(buffer_size).decode()
        received += buffer
    data = wjson.from_json(received)
    s.close()

    if data['status'] == 'failed':
        failed_on(data['payload'])
    else:
        return data['payload']


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
                 buffer_size:int=BUFFER_SIZE, host:str=TCP_IP):
        self.token = None
        self.problem_id = problem
        self.port = int(port)
        self.buffer_size = int(buffer_size)
        self.host = str(host)
        self.root = bool(root)
        self.name = str(name)
        self.registration_password = str(registration_password)
        self.known_params = {'token', 'problem', 'problem_id'}
        self.register()
        self.implement_api()


    def register(self):
        """Perform the registration on the server"""
        func = 'register_rooter' if self.root else 'register_player'
        self.token = self._send(func, name=self.name, password=self.registration_password)


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


    def _send(self, function, **kwargs):
        """Send request to the server"""
        return send(function, **kwargs)
