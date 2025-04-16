import requests

def search_epic(headers, query="XAUUSD"):
    url = "https://demo-api-capital.backend-capital.com/api/v1/markets"
    params = {"searchTerm": query}

    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    data = res.json()
    print(data)
    results = []

    for market in data['markets']:
        results.append({
            "name": market['instrumentName'],
            "epic": market['epic'],
            "expiry": market['expiry'],
            "marketStatus": market['marketStatus']
        })

    return results
