import asyncio
import json
import logging

import websockets
from django.conf import settings


logger = logging.getLogger(__name__)


async def produce_message(message: str, address: str) -> None:

    try:
        async with websockets.connect(address) as web_socket:
            json_message = json.dumps({
                'message': message,
            })
            await web_socket.send(json_message)
            await web_socket.recv()

    except ConnectionRefusedError as e:
        logger.warning(str(e))


def send_event(message: str = '', host: str = '127.0.0.1', port: int = 9000):
    """
    Функция для отправки сообщения по всем активным соединениям WebSocket
    """
    address = settings.WEB_SOCKET_SERVER_URL if settings.WEB_SOCKET_SERVER_URL else f'ws://{host}:{port}/'
    asyncio.run(produce_message(message=message, address=address))
