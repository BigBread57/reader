import asyncio
import logging

import websockets


logging.basicConfig(level='DEBUG')


class WSServer:
    """
    Класс реализует сервер обработки соединений по websocket
    """

    clients = set()

    async def register(self, web_socket: websockets.WebSocketServerProtocol) -> None:
        """
        Метод для регистрации нового соединения
        """

        self.clients.add(web_socket)
        logging.debug(f'{web_socket.remote_address} connects.')

    async def unregister(self, web_socket: websockets.WebSocketServerProtocol) -> None:
        """
        Метод для отмены регистрации соединения
        """

        self.clients.remove(web_socket)
        logging.debug(f'{web_socket.remote_address} disconnects.')

    async def send_to_clients(self, message: str) -> None:
        """
        Метод для отправки сообщения через все активные соединения
        """

        if self.clients:
            await asyncio.wait([client.send(message) for client in self.clients])

    async def distribute(self, web_socket: websockets.WebSocketServerProtocol) -> None:
        """
        Метод для отправки всех сообщений
        """

        async for message in web_socket:
            await self.send_to_clients(message)

    async def websocket_handler(self, web_socket: websockets.WebSocketServerProtocol, uri: str) -> None:
        """
        Метод обработчик события создания нового соединения
        """

        await self.register(web_socket)
        try:
            await self.distribute(web_socket)
        finally:
            await self.unregister(web_socket)


ws_server = WSServer()
server = websockets.serve(ws_server.websocket_handler, '0.0.0.0', 9000)
loop = asyncio.get_event_loop()
loop.run_until_complete(server)
loop.run_forever()

