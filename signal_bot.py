import os
import requests
import pandas as pd
from datetime import datetime

SYMBOL = os.environ.get("SYMBOL")
INTERVAL = os.environ.get("INTERVAL")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE = os.environ.get("WHATSAPP_PHONE")
WHATSAPP_API_URL = "https://whatsapp.tkwin.com.sa/api/v1/send"

LENGTH = 20
MULT = 2.0

def send_whatsapp(message):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE:
        print("Missing token or phone")
        return
    headers = {'Authorization': f'Bearer {WHATSAPP_TOKEN}', 'Content-Type': 'application/json'}
    payload = {"to": WHATSAPP_PHONE, "message": message}
    try:
        r = requests.post(WHATSAPP_API_URL, headers=headers, json=payload, timeout=10)
        print(f"WhatsApp: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def get_binance_klines(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url, timeout=10).json()
    df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_vol','trades','taker_base','taker_quote','ignore'])
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df

def calculate_signals(df):
    df['basis'] = df['close'].rolling(LENGTH).mean()
    df['dev'] = MULT * df['close'].rolling(LENGTH).std()
    df['upper'] = df['basis'] + df['dev']
    df['lower'] = df['basis'] - df['dev']
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['high_vol'] = df['volume'] > df['vol_avg']
    df['buy_signal'] = (df['close'].shift(1) < df['lower'].shift(1)) & (df['close'] > df['lower']) & df['high_vol']
    df['sell_signal'] = (df['close'].shift(1) > df['upper'].shift(1)) & (df['close'] < df['upper']) & df['high_vol']
    return df

if __name__ == "__main__":
    # 1. رسالة تأكيد التشغيل على الواتساب
    start_msg = f"✅ تم تشغيل البوت بنجاح\nالعملة: {SYMBOL}\nالفريم: {INTERVAL}\nالوقت: {datetime.now().strftime('%H:%M')}\n\nانتظر الإشارة... بيوصلك تنبيه لو ظهرت إشارة بيع أو شراء"
    send_whatsapp(start_msg)
    
    # 2. نشيك الإشارات
    df = get_binance_klines(SYMBOL, INTERVAL)
    df = calculate_signals(df)
    last = df.iloc[-1]
    
    if last['buy_signal']:
        signal_msg = f"🚀 BUY Signal {SYMBOL}\nالسعر: {last['close']:.2f}\nالفريم: {INTERVAL}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        send_whatsapp(signal_msg)
    elif last['sell_signal']:
        signal_msg = f"🔻 SELL Signal {SYMBOL}\nالسعر: {last['close']:.2f}\nالفريم: {INTERVAL}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        send_whatsapp(signal_msg)
    else:
        print(f"No signal {SYMBOL}-{INTERVAL}")
