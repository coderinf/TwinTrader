import hmac
import hashlib
import base64
import json
import time
import requests

#enter your API Key 2nd account mohan nekkanti  and Secret here.
key=""
secret=""

# python3
secret_bytes = bytes(secret, encoding='utf-8')
def place_order(pair, side, price, qnty, lvg):
# Generating a timestamp
      timeStamp = int(round(time.time() * 1000)+(5 * 60 * 60 * 1000) + (30 * 60 * 1000))

      body = {
              "timestamp":timeStamp , # EPOCH timestamp in seconds
              "order": {
              "side": side, # buy OR sell
              "pair": pair, # instrument.string
              "order_type": "market_order", # market_order OR limit_order
              "price": price, #numeric value
              "total_quantity": abs(qnty), #numerice value
              "leverage": lvg, #numerice value
              "notification": "email_notification", # no_notification OR email_notification OR push_notification
              "time_in_force": "good_till_cancel", # good_till_cancel OR fill_or_kill OR immediate_or_cancel
              "hidden": False, # True or False
              "post_only": False # True or False
              }
              }

      json_body = json.dumps(body, separators = (',', ':'))

      signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

      url = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"

      headers = {
          'Content-Type': 'application/json',
          'X-AUTH-APIKEY': key,
          'X-AUTH-SIGNATURE': signature
      }

      response = requests.post(url, data = json_body, headers = headers)
      data = response.json()
      return data
def get_active_positions():
    secret_bytes = bytes(secret, encoding='utf-8')
    time_stamp = int(round(time.time() * 1000))

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
            if item['active_pos'] != 0:
                active_positions.append(
                     item['pair'])
        return active_positions

#print(get_active_positions())
