from fastapi import FastAPI, Request
from twilio.twiml.messaging_response import MessagingResponse
import ccxt
import pandas as pd
import numpy as np
import os

app = FastAPI()

# Crypto market data fetch function
def get_signal(symbol):
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        # RSI calculation
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        last_rsi = rsi.iloc[-1]

        # Simple signal logic
        if last_rsi < 30:
            return f"BUY Signal for {symbol} (RSI: {last_rsi:.2f})"
        elif last_rsi > 70:
            return f"SELL Signal for {symbol} (RSI: {last_rsi:.2f})"
        else:
            return f"HOLD Signal for {symbol} (RSI: {last_rsi:.2f})"

    except Exception as e:
        return f"Error: {str(e)}"

@app.post("/whatsapp/inbound")
async def inbound(request: Request):
    form = await request.form()
    incoming_msg = form.get('Body').strip().upper()

    # Symbol format for Binance
    if not incoming_msg.endswith("/USDT"):
        incoming_msg += "/USDT"

    signal = get_signal(incoming_msg)

    resp = MessagingResponse()
    resp.message(signal)
    return str(resp)
