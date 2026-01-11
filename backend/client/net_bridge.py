import asyncio
import json
import websockets
from client.clipboard import read_clipboard_text, write_clipboard_text

class NetBridge:
    def __init__(self, uri: str, session_id: str, name: str):
        self.uri = uri
        self.session_id = session_id
        self.name = name
        self.ws = None

    async def connect(self):
        self.ws = await websockets.connect(self.uri)
        await self.ws.send(json.dumps({"type":"JOIN","session_id":self.session_id,"name":self.name}))
        print(f"[net] joined {self.session_id} as {self.name}")

    async def run(self):
        await self.connect()
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if msg.get("type") == "CLIPBOARD_SET":
                write_clipboard_text(msg.get("text", ""))

    async def send_clipboard(self):
        if not self.ws:
            print("[net] not connected")
            return
        text = read_clipboard_text()
        print(f"[net] sending clipboard ({len(text)} chars)")
        await self.ws.send(json.dumps({
            "type": "CLIPBOARD_SET",
            "from": self.name,
            "text": text
        }))