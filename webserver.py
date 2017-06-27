"""Implementation of the webserver, making the bridge between
client and Weldon.

"""


import json
import socketserver

import wjson
import server as weldon


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
        self._server_methods = frozenset(attr for attr in dir(self.server)
                                         if not attr.startswith('_'))

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
            ret = getattr(self.server, command)(*args, **kwargs)
            print('XINZIW:webserver:ret:', ret)
            sent = wjson.as_json(ret)
            print('KLDMQF:webserver:as_json:', sent)
            return sent
        return '{"NOPE": "Invalid command"}'



if __name__ == "__main__":
    PLAYER_PASSWORD = 'WOLOLO42'
    ROOTER_PASSWORD = 'SHUBISHI'
    server = weldon.Server(player_password=PLAYER_PASSWORD,
                           rooter_password=ROOTER_PASSWORD)
    WebInterface(server).run()
