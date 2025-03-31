import hmac
import hashlib
import json
import time
import requests

# Enter your API Key and Secret here.
key = "44ed7979643b133d4bf23ecd145c8d30cccbee6b829a4f8d"
secret = "69b9938908fab3a9965891d8d318e5db2ae8105f2d518a801273cbdf7ad4f552"

def calculate_lslp(bp, psl=5.0, lvg=5):
    return bp - (bp * psl / (lvg * 100))

def calculate_sslp(bp, psl=5.0, lvg=5):
    return bp + (bp * psl / (lvg * 100))

def get_active_positions():
    secret_bytes = bytes(secret, encoding='utf-8')
    time_stamp = int(round(time.time() * 1000)+(5 * 60 * 60 * 1000) + (30 * 60 * 1000))

    body = {
        "timestamp": time_stamp,
        "page": "1",
        "size": "10"
    }
    json_body = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions"
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }

    response = requests.post(url, data=json_body, headers=headers)
    if response.status_code == 200:
        data = response.json()
        active_positions = []
        for item in data:
            if item['active_pos'] != 0 :
                position_type = "long" if item['active_pos'] > 0 else "short"
                slp = calculate_lslp(item['avg_price'],psl=5,lvg=item['leverage']) if position_type == "long" else calculate_sslp(item['avg_price'],psl=5,lvg=item['leverage'])
                base_price = calculate_lslp(item['avg_price'], psl=4.5,lvg=item['leverage']) if position_type == "long" else calculate_sslp(item['avg_price'],psl=4.5,lvg=item['leverage'])
                active_positions.append({
                    "pair": item['pair'],
                    "type": position_type,
                    "slp": slp,
                    "active_pos": float (item['active_pos']),
                    "buy_price":float(item['avg_price']),
                    "base_price":base_price,
                    "leverage":item['leverage']

                })
        return active_positions
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []


