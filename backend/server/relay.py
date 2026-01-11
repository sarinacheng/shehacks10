import asyncio
import json
import websockets

# session_id -> set of websocket connections
SESSIONS: dict[str, set] = {}


async def broadcast(session_id: str, sender, message: dict):
    """Send message to all clients in session except sender."""
    if session_id not in SESSIONS:
        return

    dead = []
    payload = json.dumps(message)

    for ws in SESSIONS[session_id]:
        if ws is sender:
            continue
        try:
            await ws.send(payload)
        except Exception:
            dead.append(ws)

    # cleanup dead sockets
    for ws in dead:
        SESSIONS[session_id].discard(ws)


async def handler(ws):
    session_id = None
    try:
        # Expect first message to be a JOIN
        raw = await ws.recv()
        msg = json.loads(raw)

        if msg.get("type") != "JOIN" or not msg.get("session_id"):
            await ws.send(json.dumps({"type": "ERROR", "message": "First message must be JOIN with session_id"}))
            return

        session_id = str(msg["session_id"])
        SESSIONS.setdefault(session_id, set()).add(ws)

        await ws.send(json.dumps({"type": "JOINED", "session_id": session_id}))
        print(f"[relay] client joined session={session_id} clients={len(SESSIONS[session_id])}")

        # Main loop: receive and forward
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send(json.dumps({"type": "ERROR", "message": "Invalid JSON"}))
                continue

            # Optional: allow client to ping
            if msg.get("type") == "PING":
                await ws.send(json.dumps({"type": "PONG"}))
                continue

            # Forward everything else
            await broadcast(session_id, ws, msg)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if session_id and session_id in SESSIONS:
            SESSIONS[session_id].discard(ws)
            if not SESSIONS[session_id]:
                del SESSIONS[session_id]
            print(f"[relay] client left session={session_id} remaining={len(SESSIONS.get(session_id, []))}")


async def main():
    host = "0.0.0.0"
    port = 8765
    print(f"[relay] starting ws://{host}:{port}")
    async with websockets.serve(handler, host, port, ping_interval=20, ping_timeout=20):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())