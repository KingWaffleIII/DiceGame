import asyncio
import json
import websockets


async def receive_messages(websocket):
    try:
        i = 1
        while True:
            message = await websocket.recv()
            print(f"{i}: Received message: {message}\n")

            data = json.loads(message)

            match data["message"]:
                case "your roll":
                    input()
                    await websocket.send(json.dumps({}))
                case _:
                    pass

            i += 1

    except websockets.ConnectionClosed:
        print("Connection to the server closed.")


async def main():
    uri = "ws://localhost:8000/ws/game/194659/"

    async with websockets.connect(
        uri,
        extra_headers={"Authorization": "Basic dGVzdDI6dGVzdA=="},
        ping_timeout=None,
    ) as websocket:
        # Start two tasks concurrently: one for receiving messages and one for sending user input
        await receive_messages(websocket)


if __name__ == "__main__":
    asyncio.run(main())
