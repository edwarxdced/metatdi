import websocket
import json
import threading
import time
from config import WS_URL

def default_on_message(ws, message):
    data = json.loads(message)
    print("Mensaje WebSocket recibido:", data)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket cerrado")

def on_open(ws, cst, x_token, epic):
    subscribe = {
        "destination": "marketData.subscribe",
        "correlationId": "1",
        "cst": cst,
        "securityToken": x_token,
        "payload": {
            "epics": [epic.value],
            "subscriptionLevel": "L1"
        }
    }
    print(subscribe)
    ws.send(json.dumps(subscribe))

def ping_loop(ws, cst, x_token):
    while True:
        try:
            payload = {
                "destination": "ping",
                "correlationId": "1",
                "cst": cst,
                "securityToken": x_token,
            }
            ws.send(json.dumps(payload))
            print("🫀 Enviando PING...")
        except Exception as e:
            print(f"❌ Error al enviar PING: {e}")
        time.sleep(60*5)

def start_websocket(cst, x_token, epic, on_message_callback=None, ws_url=None):
    if not ws_url:
        raise ValueError("WebSocket URL (streamingHost) is required")
    
    print(f"Iniciando WebSocket con URL: {WS_URL}")
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=lambda ws: on_open(ws, cst, x_token, epic),
        on_message=on_message_callback or default_on_message,
        on_error=on_error,
        on_close=on_close,
    )

    thread = threading.Thread(target=ws.run_forever)
    thread.daemon = True
    thread.start()

    ping_thread = threading.Thread(target=ping_loop, args=(ws, cst, x_token))
    ping_thread.daemon = True
    ping_thread.start()

    return ws
