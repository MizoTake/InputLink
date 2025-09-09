import asyncio
import logging

from input_link.network.websocket_server import WebSocketServer
from input_link.network.websocket_client import WebSocketClient
from input_link.models import ControllerInputData, ButtonState, ControllerState


async def main():
    logging.basicConfig(level=logging.DEBUG)
    recv = []

    def icb(d):
        print("SERVER RECV", d.controller_number)
        recv.append(d.controller_number)

    def scb(status, data=None):
        print("SERVER STATUS", status, data)

    def ccb(status):
        print("CLIENT STATUS", status)

    server = WebSocketServer("127.0.0.1", 0, status_callback=scb, input_callback=icb)
    await server.start()
    print("PORT", server.port)

    client = WebSocketClient("127.0.0.1", server.port, status_callback=ccb)
    await client.start()
    await asyncio.sleep(0.5)

    for i in [1, 2, 3]:
        d = ControllerInputData(controller_number=i, controller_id=str(i), buttons=ButtonState(), axes=ControllerState())
        await client.send_controller_input(d)

    await asyncio.sleep(1.0)
    print("RECV LEN", len(recv))
    await client.stop()
    await server.stop()


if __name__ == "__main__":
    asyncio.run(main())

