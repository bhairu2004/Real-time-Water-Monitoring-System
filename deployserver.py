from quart import Quart, websocket, jsonify
from quart import request
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

@app.route("/esp32", methods=["POST"])
async def esp32_post():
    try:
        data = await request.get_json()  # ESP32 will send JSON
        latest_data["temperature"] = float(data.get("temperature", 0))
        latest_data["tds"] = float(data.get("tds", 0))
        latest_data["ph"] = float(data.get("ph", 0))
    # Broadcast to all frontends
        for client in list(connected_frontends):
            try:
                await client.send(f"{latest_data['temperature']},{latest_data['tds']},{latest_data['ph']}")
            except:
                connected_frontends.remove(client)
        # Optionally: Broadcast to WebSocket frontends here
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
