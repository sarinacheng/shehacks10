import asyncio
import json
import sys

import websockets

from clipboard import read_clipboard_text, write_clipboard_text

async def run(uri: str, session_id: str, name: str):
    async with websockets.connect(uri) as ws:
        # Join session
        await ws.send(json.dumps({"type": "JOIN", "session_id": session_id, "name": name}))
        print(f"[{name}] joined session={session_id} @ {uri}")
        print("Commands: /copy (send clipboard), /quit")

        async def receiver():
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    msg = {"type": "RAW", "text": raw}

                mtype = msg.get("type")

                if mtype == "CLIPBOARD_SET":
                    text = msg.get("text", "")
                    write_clipboard_text(text)
                    print(f"\n[{name}] ✅ clipboard updated ({len(text)} chars)\n> ", end="", flush=True)
                else:
                    print(f"\n[{name}] RECV -> {msg}\n> ", end="", flush=True)

        async def sender():
            loop = asyncio.get_running_loop()
            while True:
                line = await loop.run_in_executor(None, lambda: input("> "))
                cmd = line.strip().lower()

                if cmd in ("/quit", "/exit"):
                    print(f"[{name}] exiting.")
                    return

                if cmd == "/copy":
                    text = read_clipboard_text()
                    await ws.send(json.dumps({"type": "CLIPBOARD_SET", "from": name, "text": text}))
                    print(f"[{name}] 📤 sent clipboard ({len(text)} chars)")
                    continue

                # normal chat message
                await ws.send(json.dumps({"type": "MSG", "from": name, "text": line}))

        await asyncio.gather(receiver(), sender())


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client/network_client.py wss://<REPL_URL> <session_id> <name>")
        raise SystemExit(1)

    uri, session_id, name = sys.argv[1], sys.argv[2], sys.argv[3]
    asyncio.run(run(uri, session_id, name))
