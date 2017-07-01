"""Implementation of the webserver, making the bridge between
client and Weldon.

"""


import json
import socketserver

import wjson
import server as weldon
from commons import ServerError


PORT = 6519
BUFFER_SIZE = 1024


class WebInterface:

    def __init__(self, server, ip:str='127.0.0.1', port:int=PORT,
                 buffer_size:int=BUFFER_SIZE):
        self.server = server
        self._ip = str(ip)
        self._port = int(port)
        self._buffer_size = int(buffer_size)
        self._continue = True
        self._server_methods = dict(self.server.api_methods())

    def run(self):
        class TCPHandler(socketserver.StreamRequestHandler):
            """The request handler class for our server.

            It is instantiated once per connection to the server, and must
            override the handle() method to implement communication to the
            client.

            See https://docs.python.org/3.5/library/socketserver.html#module-socketserver

            """
            def handle(slf):
                slf.wfile.write(self.handle(slf.rfile.readline().strip().decode()).encode())

        server = socketserver.TCPServer((self._ip, self._port), TCPHandler)
        server.serve_forever()


    def handle(self, data:str) -> str:
        """Handle given data, return the data to return"""
        command, args, kwargs = wjson.from_json(data)
        if command in self._server_methods:
            try:
                data = {
                    'status': 'success',
                    'payload': getattr(self.server, command)(*args, **kwargs)
                }
            except ServerError as err:
                print('ServerError:', '|'.join(map(str, err.args)))
                data = {'status': 'failed', 'payload': err.args[0]}
            sent = wjson.as_json(data)
            return sent
        return '{"status":"failed","payload":"Invalid command."}'



if __name__ == "__main__":
    PLAYER_PASSWORD = 'WOLOLO42'
    ROOTER_PASSWORD = 'SHUBISHI'
    server = weldon.Server(player_password=PLAYER_PASSWORD,
                           rooter_password=ROOTER_PASSWORD)
    WebInterface(server).run()
