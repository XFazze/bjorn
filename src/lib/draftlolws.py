import websocket
import base64
import os
import json

class DraftLolWebSocket:
    def __init__(self):
        self.websocket_key = base64.b64encode(os.urandom(16)).decode('utf-8')
        self.headers = {
            "Host": "draftlol.dawe.gg",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Upgrade": "websocket",
            "Origin": "https://draftlol.dawe.gg",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Key": self.websocket_key,
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "Connection": "Upgrade",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en,en-US;q=0.9,sv;q=0.6,fr;q=0.5"
        }
        self.ws = websocket.WebSocketApp("wss://draftlol.dawe.gg/",
                                         header=self.headers,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        
        self.closed = False
        self.message = "Failed to get draftlol data"

    def on_message(self, ws, message):
        print("Received message: ", message)
        if "roomcreated" in message:
            try:
                message_json = json.loads(message)
                base = f"https://draftlol.dawe.gg/{message_json['roomId']}"
                bot_msg_string = "Spectator: " + base + '\n'
                bot_msg_string += "Blue: " + base + '/' + message_json["bluePassword"] + '\n'
                bot_msg_string += "Red: " + base + '/' + message_json["redPassword"]
                self.message = bot_msg_string
            except json.JSONDecodeError:
                print("Can't decode JSON")
            ws.close()

    def force_close(self):
        if (not self.closed):
            self.ws.close()

    def on_error(self, ws, error):
        print("Error: ", error)

    def on_close(self, ws, close_status_code, close_msg):
        self.closed = True
        print("### closed ###")

    def on_open(self, ws):
        print("Connection opened")
        message = {
            "type": "createroom",
            "blueName": "Blue",
            "redName": "Red",
            "disabledTurns": [],
            "disabledChamps": [],
            "timePerPick": 30,
            "timePerBan": 30
        }
        ws.send(json.dumps(message))

    def run(self):
        self.ws.on_open = self.on_open
        self.ws.run_forever()
