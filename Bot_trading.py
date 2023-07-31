import ccxt
import pandas as pd
import numpy as np

# Configuración inicial
exchange = ccxt.binance()  # Selecciona el intercambio (en este caso, Binance)
symbol = 'BTC/USDT'  # Selecciona el par de trading
timeframe = '1d'  # Marco temporal para los datos históricos
short_window = 20  # Ventana de tiempo para la media móvil corta
long_window = 50  # Ventana de tiempo para la media móvil larga
threshold = 0.02  # Umbral para la generación de señales de compra/venta
quantity = 0.001  # Cantidad de criptomoneda a operar

def fetch_historical_data(symbol, timeframe, limit):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def calculate_signals(df, short_window, long_window, threshold):
    df['sma_short'] = df['close'].rolling(window=short_window).mean()
    df['sma_long'] = df['close'].rolling(window=long_window).mean()
    df['signal'] = np.where(df['sma_short'] > df['sma_long'] * (1 + threshold), 1,
                            np.where(df['sma_short'] < df['sma_long'] * (1 - threshold), -1, 0))
    df['position'] = df['signal'].diff()
    df.dropna(subset=['position'], inplace=True)
    return df

def execute_trades(symbol, position):
    if position > 0:
        # Generar señal de compra y enviar una orden de compra al intercambio
        order = exchange.create_market_buy_order(symbol, quantity)
        print("Orden de compra realizada:", order)
    elif position < 0:
        # Generar señal de venta y enviar una orden de venta al intercambio
        order = exchange.create_market_sell_order(symbol, quantity)
        print("Orden de venta realizada:", order)

def monitor_and_track(symbol):
    # Monitoreo y seguimiento
    open_orders = exchange.fetch_open_orders(symbol)
    print("Órdenes abiertas:", open_orders)
    account_balance = exchange.fetch_balance()['total'][symbol.split('/')[1]]
    print("Balance de la cuenta:", account_balance)

def run_bot():
    # Obtención de datos históricos
    df = fetch_historical_data(symbol, timeframe, limit=1000)

    if df is not None:
        while True:
            # Cálculo de señales y ejecución de operaciones
            df = calculate_signals(df, short_window, long_window, threshold)

            for _, row in df.iterrows():
                execute_trades(symbol, row['position'])

            monitor_and_track(symbol)

            # Actualización de datos históricos
            df_new = fetch_historical_data(symbol, timeframe, limit=short_window)
            if df_new is not None:
                df = pd.concat([df, df_new])
                df = df.iloc[-1000:]  # Mantener solo los últimos 1000 datos

# Ejecución del bot
if __name__ == "__main__":
    run_bot()
