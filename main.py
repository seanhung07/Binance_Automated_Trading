from binance.client import Client
from binance.exceptions import BinanceAPIException
import json, config
from flask import Flask, request, abort
import time
api_key = config.API_KEY
api_secret= config.API_SECRET
client = Client(api_key=api_key,api_secret=api_secret)
app = Flask(__name__)
def closeposition(price,symbol):
    check = client.futures_account()['positions']
    for i in check:
        if i['symbol'] == symbol:
            if float(i['positionAmt']) != 0:
                quan = round(float(i['positionAmt']),3)
                if quan < 0:
                    try:
                        with open("log.txt", "a") as f:
                            f.write(f"Close Short: {i['symbol']} quantity {quan} price {price} (HERE 1)\n")
                        print(f"Close: {i['symbol']} ")
                        client.futures_create_order(symbol=symbol, side='BUY',type='MARKET',quantity=abs(quan))
                    except BinanceAPIException as e:
                        with open("log.txt", "a") as f:
                            f.write(f"status: {e.status_code} message: {e.message} (HERE 2)\n ")
                else:
                    try:
                        with open("log.txt", "a") as f:
                            f.write(f"Close Long: {i['symbol']} quantity {quan} price {price} (HERE 3)\n")
                        print(f"Close: {i['symbol']} ")
                        client.futures_create_order(symbol=symbol, side='SELL',type='MARKET',quantity=abs(quan))
                    except BinanceAPIException as e:
                        with open("log.txt", "a") as f:
                            f.write(f"status: {e.status_code} message: {e.message} (HERE 4)\n")
            else:
                continue

@app.route('/webhook', methods=['POST'])
def webhook():
    queue = []

    # get current USDT asset
    try:
        equity = float(client.futures_account()['availableBalance'])
        coin_detail = client.futures_account()['positions']
    except BinanceAPIException as e:
        with open("log.txt", "a") as f:
            f.write(f"status: {e.status_code} message: {e.message} (HERE 5)\n")

    if request.method == 'POST':
        data = json.loads(request.data)
        symbol = data['ticker'].replace("PERP","")
        action = data['action'].strip().lower()
        leverage = int(data['leverage'])
        price = float(data['price'])
        kelly = float(data['kelly'])
        margin = equity*kelly
        quan = round((margin*leverage)/float(price),1)
        try:
            client.futures_change_leverage(symbol=symbol, leverage=leverage)
        except BinanceAPIException as e:
            with open("log.txt", "a") as f:
                f.write(f"status: {e.status_code} message: {e.message} (HERE Leverage)\n")
        # change margin type
        for i in coin_detail:
            if i['symbol'] == symbol:
                if i['isolated'] == False:
                    try:
                        client.futures_change_margin_type(symbol=symbol,marginType='ISOLATED')
                    except BinanceAPIException as e:
                        with open("log.txt", "a") as f:
                            f.write(f"status: {e.status_code} message: {e.message} (HERE 6)\n")
                else:
                    continue

        # open long position
        if action == "open long":
                time.sleep(1)
                try:
                    client.futures_create_order(symbol=symbol, side='BUY',type='MARKET',quantity=quan)
                    with open("log.txt", "a") as f:
                        f.write(f"LONG: {symbol} @ { price } quantity: {quan} margin: {margin} leverage: {leverage} \n")
                    print(f"LONG: {symbol} @ { price } quantity {quan}")
                except BinanceAPIException as e:
                    with open("log.txt", "a") as f:
                        f.write(f"status: {e.status_code} message: {e.message} (HERE 7) \n")

        # open short poistion
        elif action == "open short":
                time.sleep(1)
                try:
                    client.futures_create_order(symbol=symbol, side='SELL',type='MARKET',quantity=quan)
                    with open("log.txt", "a") as f:
                        f.write(f"SHORT: {symbol} @ { price } quantity {quan} margin: {margin} leverage: {leverage} \n")
                    print(f"SHORT: {symbol} @ { price } quantity {quan}")
                except BinanceAPIException as e:
                    with open("log.txt", "a") as f:
                        f.write(f"status: {e.status_code} message: {e.message} (HERE 8)\n")

        # get close position
        else:
            closeposition(price, symbol)
        return 'success', 200
    else:
        abort(400)

@app.route('/test', methods=['POST'])
def test():
    if request.method == 'POST':
        try:
            print('fuck me')
            with open("log.txt", "a") as f:
                f.write("test")
            print("after", request.json)
        except BinanceAPIException as e:
            with open("log.txt", "a") as f:
                f.write(f"status: {e.status_code} message: {e.message} \n")
        return 'success', 200
    else:
        abort(400)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 80)
