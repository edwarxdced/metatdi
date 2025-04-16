# capital_api.py

import requests

BASE_URL = "https://demo-api-capital.backend-capital.com"


def login(email: str, password: str, api_key: str):
    url = f"{BASE_URL}/api/v1/session"
    headers = {
        "X-CAP-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "identifier": email,
        "password": password
    }

    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()

    # Los tokens vienen en los headers
    cst = res.headers.get("CST")
    security_token = res.headers.get("X-SECURITY-TOKEN")
    raw_host = res.json().get("streamingHost")
    streaming_host = raw_host.rstrip("/") + "/connection"

    if not cst or not security_token:
        raise Exception("Login exitoso pero faltan tokens de autenticación")

    session_headers = {
        "X-CAP-API-KEY": api_key,
        "CST": cst,
        "X-SECURITY-TOKEN": security_token,
        "Content-Type": "application/json"
    }

    return session_headers, cst, security_token, streaming_host
