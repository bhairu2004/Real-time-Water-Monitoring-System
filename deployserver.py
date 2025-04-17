from quart import Quart, websocket, jsonify
import asyncio

app = Quart(__name__)

connected_frontends = set()
latest_data = {
    "temperature": 0.0,
    "tds": 0.0,
    "ph": 0.0
}

@app.route("/healthz")
async def healthz():
    return "OK", 200

@app.websocket("/frontend")
async def frontend_ws():
    connected_frontends.add(websocket._get_current_object())
    await websocket.send(f"{latest_data['temperature']},{latest_data['tds']},{latest_data['ph']}")
    try:
        while True:
            await asyncio.sleep(3600)  # Keep alive
    finally:
        connected_frontends.remove(websocket._get_current_object())

@app.websocket("/esp32")
async def esp32_ws():
    while True:
        message = await websocket.receive()
        try:
            t, tds, ph = map(float, message.strip().split(","))
            latest_data["temperature"] = t
            latest_data["tds"] = tds
            latest_data["ph"] = ph
            # Broadcast to all frontends
            for client in list(connected_frontends):
                try:
                    await client.send(message)
                except:
                    connected_frontends.remove(client)
        except ValueError:
            print("Invalid format from ESP32.")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
