import socketio
import hmac
import hashlib
import json
import asyncio
from datetime import datetime
import requests
from tenacity import retry, wait_fixed, stop_after_attempt, RetryError
import time
import ops
import positionsdata
socketEndpoint = 'wss://stream.coindcx.com'
# API key and secret
key=""
secret=""
# Convert the secret key to bytes
secret_bytes = bytes(secret1, encoding='utf-8')
channelName = "coindcx"
body = {"channel": channelName}
json_body = json.dumps(body, separators=(',', ':'))
signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

# Updated SocketClient class
class SocketClient:
    def __init__(self, socket_endpoint: str, key: str, secret: str, pair: str, position_type: str, slp: float,
                 active_pos: float, leverage: float, buy_price: float ,base_price: float):
        self.socket_endpoint = socket_endpoint
        self.key = key
        self.secret = secret
        self.pair = pair
        self.position_type = position_type
        self.slp = slp
        self.active_pos = active_pos
        self.leverage = leverage
        self.buy_price = buy_price
        self.base_price = base_price
        self.reversed = self.pair in ops.get_active_positions()
        self.sio = socketio.AsyncClient()
        self.connected = False  # Track connection state

    async def connect(self):
        @self.sio.event
        async def connect():
            self.connected = True
            #print(f"I'm connected for pair {self.pair} ({self.position_type})!")
            current_time = datetime.now()
            #print(f"Connected Time for {self.pair}: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            await self.sio.emit('join', {'channelName': "coindcx", 'authSignature': signature, 'apiKey': self.key})
            await self.sio.emit('join', {'channelName': f"{self.pair}@prices-futures"})

        @self.sio.on('price-change')
        async def on_message(response):
            current_time = datetime.now()
            #print(f"Price change for {self.pair} ({self.position_type}) at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            data = json.loads(response['data'])
            self.capture(data['p'])

        await self.sio.connect(self.socket_endpoint, transports='websocket')
        asyncio.create_task(self.ping_task())
        await self.sio.wait()

    async def ping_task(self):
        while True:
            await asyncio.sleep(25)
            try:
                await self.sio.emit('ping', {'data': 'Ping message'})
            except Exception as e:
                print(f"Error sending ping for pair {self.pair}: {e}")

    def capture(self, price):
        #print(f"Price change for {self.pair} ({self.position_type}) is {price}")
        try:
            if self.position_type == "long" and not self.reversed and float(price) <= self.slp:
                #print(f"Price {price} is below SLP for long position on {self.pair}")
                # Place a reverse order (short) with the same quantity and double leverage
                ops.place_order(self.pair, "sell", price, self.active_pos, self.leverage)
                self.reversed = True

            elif self.position_type == "short" and not self.reversed and float(price) >= self.slp:
                #print(f"Price {price} is above SLP for short position on {self.pair}")
                # Place a reverse order (long) with the same quantity and double leverage
                ops.place_order(self.pair, "buy", price, self.active_pos, self.leverage)
                self.reversed = True


            elif self.reversed and float(price) >= self.base_price:
                #print(f"Price {price} reached base price for reversed position on {self.pair}")
                # Exit the reverse order
                if self.position_type == "long":
                    ops.place_order(self.pair, "buy", price, self.active_pos, self.leverage)
                elif self.position_type == "short":
                    ops.place_order(self.pair, "sell", price, self.active_pos, self.leverage)
                self.reversed = False


        except Exception as e:
          print(f"Error in capture method for pair {self.pair}: {e}")

    async def disconnect(self):
        if self.connected:
            try:
                await self.sio.disconnect()
                self.connected = False
                #print(f"Disconnected for pair {self.pair} ({self.position_type})")
            except Exception as e:
              print(f"Error disconnecting for pair {self.pair}: {e}")


# Updated monitor_new_positions and main function

@retry(wait=wait_fixed(5), stop=stop_after_attempt(5))
def get_active_positions():

    try:
        return positionsdata.get_active_positions()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching active positions: {e}")
        raise


async def monitor_new_positions(clients, connected_pairs):
    while True:
        await asyncio.sleep(30)  # Check for new positions every 30 seconds
        try:
            pairs = get_active_positions()
        except RetryError as e:
            print("Max retries exceeded for fetching active positions")
            continue

        new_pairs = set((pair['pair'], pair['type']) for pair in pairs) - set(connected_pairs)
        for pair, position_type in new_pairs:
            #print(f"New pair detected: {pair} ({position_type}), connecting...")
            client = SocketClient(socketEndpoint, key1, secret1, pair, position_type, pair['slp'], pair['active_pos'],
                                  pair['leverage'], pair['avg_price'])
            clients.append(client)
            connected_pairs.append((pair, position_type))
            asyncio.create_task(client.connect())

        # Disconnect clients for pairs no longer in active positions
        for client in clients[:]:  # Iterate over a copy to safely modify original list
            if (client.pair, client.position_type) not in [(pair['pair'], pair['type']) for pair in pairs]:
                await client.disconnect()
                clients.remove(client)
                connected_pairs.remove((client.pair, client.position_type))


async def main():
    try:
        pairs = get_active_positions()  # Retrieve the initial list of pairs from ACTIVEPOS with retry logic
    except RetryError as e:
        print("Max retries exceeded for fetching active positions")
        return

    clients = [SocketClient(socketEndpoint, key1, secret1, pair['pair'], pair['type'], pair['slp'], pair['active_pos'],
                            pair['leverage'],pair['buy_price'], pair['base_price']) for pair in pairs]
    connected_pairs = [(pair['pair'], pair['type']) for pair in pairs]
    tasks = [client.connect() for client in clients]

    # Add monitor_new_positions as a concurrent task
    tasks.append(monitor_new_positions(clients, connected_pairs))

    await asyncio.gather(*tasks)


asyncio.run(main())
