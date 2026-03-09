import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for web use
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime
import pytz
import io
import base64
import time

# Settings
INTERVAL = "5m"   # 5-minute interval for data fetching
PERIOD = "3d"    # 60 days of historical data
# DATA_LIMIT = 17280  # Approx 60 days of 5-minute data (12 bars/hour * 24 hours * 60 days)
LOCAL_TIMEZONE = 'Asia/Dhaka'  # Timezone for +06:00 (e.g., Bangladesh)
MAJORITY_THRESHOLD = 0.50  # Minimum percentage (60%) for majority candle direction
ENABLE_BACKTESTING = False  # Global variable to enable or disable backtesting

# Indicator parameters optimized for 5-minute chart
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
ADX_PERIOD = 14
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3
STOCH_SMOOTH = 3
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20
EMA_FAST_PERIOD = 10
EMA_SLOW_PERIOD = 20
STOCHASTIC_THRESHOLD = 50  # Added for Strategy 1
ATR_PERIOD = 14  # ATR period for volatility measurement
ICHIMOKU_PARAMS = {"tenkan_period": 9, "kijun_period": 26, "senkou_b_period": 52}  # Ichimoku Cloud parameters

# Risk Management Settings (ATR Multipliers)
ATR_SL_MULTIPLIER = 1.5  # Stop Loss multiplier (1.5x ATR)
ATR_TP_MULTIPLIER = 2.0  # Take Profit multiplier (2.0x ATR for positive Risk:Reward)

# Constants you might be using
MAX_RETRIES = 3  # Number of retries before giving up
RETRY_DELAY = 5  # Seconds to wait between retries

def calculate_rsi(df, period=RSI_PERIOD):
    """Calculate Relative Strength Index (RSI)."""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(df, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL):
    """Calculate MACD, Signal Line, and Histogram."""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    
    return macd, signal_line, histogram

def calculate_bollinger_bands(df, period=BB_PERIOD, std_dev=BB_STD):
    """Calculate Bollinger Bands."""
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    bb_upper = sma + (std * std_dev)
    bb_lower = sma - (std * std_dev)
    
    return bb_upper, sma, bb_lower

def calculate_adx(df, period=ADX_PERIOD):
    """Calculate Average Directional Index (ADX), +DI, -DI."""
    if len(df) < period * 2:
        return None, None, None

    high = df['high']
    low = df['low']
    close = df['close']
    
    tr_list = []
    plus_dm_list = []
    minus_dm_list = []

    for i in range(1, len(df)):
        high_curr = high.iloc[i]
        low_curr = low.iloc[i]
        close_prev = close.iloc[i-1]
        high_prev = high.iloc[i-1]
        low_prev = low.iloc[i-1]

        # True Range (TR)
        tr1 = high_curr - low_curr
        tr2 = abs(high_curr - close_prev)
        tr3 = abs(low_curr - close_prev)
        tr = max(tr1, tr2, tr3)

        # Directional Movement
        up_move = high_curr - high_prev
        down_move = low_prev - low_curr
        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0

        tr_list.append(tr)
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    if len(tr_list) < period:
        return None, None, None

    # Smooth TR, +DM, -DM
    smoothed_tr = []
    smoothed_plus_dm = []
    smoothed_minus_dm = []

    smoothed_tr.append(sum(tr_list[:period]))
    smoothed_plus_dm.append(sum(plus_dm_list[:period]))
    smoothed_minus_dm.append(sum(minus_dm_list[:period]))

    for i in range(period, len(tr_list)):
        smoothed_tr.append(smoothed_tr[-1] - (smoothed_tr[-1] / period) + tr_list[i])
        smoothed_plus_dm.append(smoothed_plus_dm[-1] - (smoothed_plus_dm[-1] / period) + plus_dm_list[i])
        smoothed_minus_dm.append(smoothed_minus_dm[-1] - (smoothed_minus_dm[-1] / period) + minus_dm_list[i])

    plus_di = []
    minus_di = []
    for i in range(len(smoothed_tr)):
        if smoothed_tr[i] == 0:
            plus_di.append(0)
            minus_di.append(0)
        else:
            plus_di.append((smoothed_plus_dm[i] / smoothed_tr[i]) * 100)
            minus_di.append((smoothed_minus_dm[i] / smoothed_tr[i]) * 100)

    dx_list = []
    for i in range(len(plus_di)):
        di_sum = plus_di[i] + minus_di[i]
        if di_sum == 0:
            dx_list.append(0)
        else:
            dx_list.append(abs(plus_di[i] - minus_di[i]) / di_sum * 100)

    adx_list = []
    adx_list.append(sum(dx_list[:period]) / period)
    for i in range(period, len(dx_list)):
        adx_list.append((adx_list[-1] * (period - 1) + dx_list[i]) / period)

    return (
        pd.Series(adx_list, index=df.index[-len(adx_list):]),
        pd.Series(plus_di, index=df.index[-len(plus_di):]),
        pd.Series(minus_di, index=df.index[-len(minus_di):])
    )

def calculate_stochastic(df, k_period=STOCH_K_PERIOD, d_period=STOCH_D_PERIOD, smooth=STOCH_SMOOTH):
    """Calculate Stochastic Oscillator (%K and %D)."""
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    
    k = 100 * (df['close'] - low_min) / (high_max - low_min)
    k_smooth = k.rolling(window=smooth).mean()
    d = k_smooth.rolling(window=d_period).mean()
    
    return k_smooth, d

def calculate_ema(df, period):
    """Calculate Exponential Moving Average (EMA)."""
    return df['close'].ewm(span=period, adjust=False).mean()

def calculate_atr(df, period=ATR_PERIOD):
    """Calculate Average True Range (ATR)."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_ichimoku(df, tenkan_period=9, kijun_period=26, senkou_b_period=52):
    """Calculate Ichimoku Cloud indicators."""
    # Tenkan-sen (Conversion Line)
    tenkan_high = df['high'].rolling(window=tenkan_period).max()
    tenkan_low = df['low'].rolling(window=tenkan_period).min()
    tenkan = (tenkan_high + tenkan_low) / 2
    
    # Kijun-sen (Base Line)
    kijun_high = df['high'].rolling(window=kijun_period).max()
    kijun_low = df['low'].rolling(window=kijun_period).min()
    kijun = (kijun_high + kijun_low) / 2
    
    # Senkou Span A (Leading Span A)
    senkou_a = ((tenkan + kijun) / 2).shift(kijun_period)
    
    # Senkou Span B (Leading Span B)
    senkou_b_high = df['high'].rolling(window=senkou_b_period).max()
    senkou_b_low = df['low'].rolling(window=senkou_b_period).min()
    senkou_b = ((senkou_b_high + senkou_b_low) / 2).shift(kijun_period)
    
    # Chikou Span (Lagging Span)
    chikou = df['close'].shift(-kijun_period)
    
    return {
        'tenkan': tenkan,
        'kijun': kijun,
        'senkou_a': senkou_a,
        'senkou_b': senkou_b,
        'chikou': chikou
    }

def generate_signal(df):
    """Generate trading signal using multiple indicators and a voting system."""
    # Calculate indicators
    rsi = calculate_rsi(df)
    macd, signal_line, histogram = calculate_macd(df)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df)
    adx, plus_di, minus_di = calculate_adx(df)
    k, d = calculate_stochastic(df)
    ema_fast = calculate_ema(df, EMA_FAST_PERIOD)
    ema_slow = calculate_ema(df, EMA_SLOW_PERIOD)
    atr = calculate_atr(df)
    ichimoku = calculate_ichimoku(df, **ICHIMOKU_PARAMS)
    
    # Extract latest values
    latest_rsi = rsi.iloc[-1] if not rsi.isna().iloc[-1] else None
    latest_macd = macd.iloc[-1] if not macd.isna().iloc[-1] else None
    latest_signal = signal_line.iloc[-1] if not signal_line.isna().iloc[-1] else None
    latest_histogram = histogram.iloc[-1] if not histogram.isna().iloc[-1] else None
    latest_bb_upper = bb_upper.iloc[-1] if not bb_upper.isna().iloc[-1] else None
    latest_bb_middle = bb_middle.iloc[-1] if not bb_middle.isna().iloc[-1] else None
    latest_bb_lower = bb_lower.iloc[-1] if not bb_lower.isna().iloc[-1] else None
    latest_adx = adx.iloc[-1] if adx is not None and not adx.isna().iloc[-1] else None
    latest_plus_di = plus_di.iloc[-1] if plus_di is not None and not plus_di.isna().iloc[-1] else None
    latest_minus_di = minus_di.iloc[-1] if minus_di is not None and not minus_di.isna().iloc[-1] else None
    latest_k = k.iloc[-1] if not k.isna().iloc[-1] else None
    latest_d = d.iloc[-1] if not d.isna().iloc[-1] else None
    latest_ema_fast = ema_fast.iloc[-1] if not ema_fast.isna().iloc[-1] else None
    latest_ema_slow = ema_slow.iloc[-1] if not ema_slow.isna().iloc[-1] else None
    latest_atr = atr.iloc[-1] if not atr.isna().iloc[-1] else None
    latest_tenkan = ichimoku['tenkan'].iloc[-1] if not ichimoku['tenkan'].isna().iloc[-1] else None
    latest_kijun = ichimoku['kijun'].iloc[-1] if not ichimoku['kijun'].isna().iloc[-1] else None
    latest_senkou_a = ichimoku['senkou_a'].iloc[-1] if not ichimoku['senkou_a'].isna().iloc[-1] else None
    latest_senkou_b = ichimoku['senkou_b'].iloc[-1] if not ichimoku['senkou_b'].isna().iloc[-1] else None
    latest_chikou = ichimoku['chikou'].iloc[-1] if not ichimoku['chikou'].isna().iloc[-1] else None
    latest_price = df['close'].iloc[-1]
    
    # Check for valid data, excluding chikou as it may be None due to forward shift
    required_values = [
        latest_rsi, latest_macd, latest_signal, latest_histogram, latest_bb_upper,
        latest_bb_middle, latest_bb_lower, latest_adx, latest_plus_di, latest_minus_di,
        latest_k, latest_d, latest_ema_fast, latest_ema_slow, latest_atr,
        latest_tenkan, latest_kijun, latest_senkou_a, latest_senkou_b
    ]
    if any(v is None for v in required_values):
        print("Indicator Values and Signals: Data Incomplete")
        print(f"RSI: {latest_rsi}")
        print(f"MACD: {latest_macd}, Signal: {latest_signal}, Histogram: {latest_histogram}")
        print(f"Bollinger Bands - Upper: {latest_bb_upper}, Middle: {latest_bb_middle}, Lower: {latest_bb_lower}")
        print(f"ADX: {latest_adx}, +DI: {latest_plus_di}, -DI: {latest_minus_di}")
        print(f"Stochastic - K: {latest_k}, D: {latest_d}")
        print(f"EMA - Fast: {latest_ema_fast}, Slow: {latest_ema_slow}")
        print(f"ATR: {latest_atr}")
        print(f"Ichimoku - Tenkan: {latest_tenkan}, Kijun: {latest_kijun}, Senkou A: {latest_senkou_a}, Senkou B: {latest_senkou_b}, Chikou: {latest_chikou}")
        print("Signal Generation Failed: Missing required indicator values")
        return {
            "direction": "No clear prediction available",
            "accuracy": "N/A",
            "indicator_signals": {},
            "indicator_values": {},
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None
        }

    # Initialize signals and accuracies
    signals = {}
    accuracies = {}
    Bullish = '<span style="color:green"><b>Bullish</b></span>'
    Bearish = '<span style="color:red"><b>Bearish</b></span>'
    Neutral = '<span><b>Neutral</b></span>'

    # RSI Signal
    if latest_rsi < RSI_OVERSOLD:
        signals['RSI'] = Bullish
        accuracies['RSI'] = min(95, max(60, int(100 - (latest_rsi - RSI_OVERSOLD) * 2)))
    elif latest_rsi > RSI_OVERBOUGHT:
        signals['RSI'] = Bearish
        accuracies['RSI'] = min(95, max(60, int(100 - (RSI_OVERBOUGHT - latest_rsi) * 2)))
    else:
        signals['RSI'] = Neutral
        accuracies['RSI'] = 50

    # MACD Signal
    if latest_macd > latest_signal and latest_histogram > 0:
        signals['MACD'] = Bullish
        accuracies['MACD'] = min(95, max(60, int(50 + abs(latest_histogram) * 1000)))
    elif latest_macd < latest_signal and latest_histogram < 0:
        signals['MACD'] = Bearish
        accuracies['MACD'] = min(95, max(60, int(50 + abs(latest_histogram) * 1000)))
    else:
        signals['MACD'] = Neutral
        accuracies['MACD'] = 50

    # Bollinger Bands Signal
    bb_width = latest_bb_upper - latest_bb_lower
    if latest_price > latest_bb_upper and latest_price > latest_bb_middle:
        signals['Bollinger Bands'] = Bullish
        accuracies['Bollinger Bands'] = min(95, max(60, int(50 + ((latest_price - latest_bb_upper) / bb_width) * 100)))
    elif latest_price < latest_bb_lower and latest_price < latest_bb_middle:
        signals['Bollinger Bands'] = Bearish
        accuracies['Bollinger Bands'] = min(95, max(60, int(50 + ((latest_bb_lower - latest_price) / bb_width) * 100)))
    else:
        signals['Bollinger Bands'] = Neutral
        accuracies['Bollinger Bands'] = 50

    # ADX Signal
    min_di_difference = 5
    if latest_adx > 25 and abs(latest_plus_di - latest_minus_di) > min_di_difference:
        if latest_plus_di > latest_minus_di and latest_price > latest_ema_fast:
            signals['ADX'] = Bullish
            accuracies['ADX'] = min(90, max(60, int(50 + (latest_adx - 25) * 1.5)))
        elif latest_minus_di > latest_plus_di and latest_price < latest_ema_fast:
            signals['ADX'] = Bearish
            accuracies['ADX'] = min(90, max(60, int(50 + (latest_adx - 25) * 1.5)))
        else:
            signals['ADX'] = Neutral
            accuracies['ADX'] = 50
    else:
        signals['ADX'] = Neutral
        accuracies['ADX'] = 50

    # Stochastic Signal
    if latest_k < STOCH_OVERSOLD and latest_d < STOCH_OVERSOLD and latest_k > latest_d:
        signals['Stochastic'] = Bullish
        accuracies['Stochastic'] = min(95, max(60, int(100 - (latest_k - STOCH_OVERSOLD) * 2)))
    elif latest_k > STOCH_OVERBOUGHT and latest_d > STOCH_OVERBOUGHT and latest_k < latest_d:
        signals['Stochastic'] = Bearish
        accuracies['Stochastic'] = min(95, max(60, int(100 - (STOCH_OVERBOUGHT - latest_k) * 2)))
    else:
        signals['Stochastic'] = Neutral
        accuracies['Stochastic'] = 50

    # EMA Signal
    if latest_ema_fast > latest_ema_slow and latest_price > latest_ema_fast:
        signals['EMA'] = Bullish
        accuracies['EMA'] = min(95, max(60, int(50 + abs(latest_price - latest_ema_fast) / latest_price * 1000)))
    elif latest_ema_slow > latest_ema_fast and latest_price < latest_ema_fast:
        signals['EMA'] = Bearish
        accuracies['EMA'] = min(95, max(60, int(50 + abs(latest_price - latest_ema_fast) / latest_price * 1000)))
    else:
        signals['EMA'] = Neutral
        accuracies['EMA'] = 50

    # ATR Signal
    atr_threshold = atr.iloc[-10:-1].median() if len(atr) >= 10 else 0.0005
    if latest_atr > atr_threshold:
        signals['ATR'] = Bullish if latest_ema_fast > latest_ema_slow else Bearish
        accuracies['ATR'] = min(90, max(60, int(50 + (latest_atr / atr_threshold) * 20)))
    else:
        signals['ATR'] = Neutral
        accuracies['ATR'] = 50

    # Ichimoku Cloud Signal (exclude chikou from decision)
    cloud_top = max(latest_senkou_a, latest_senkou_b)
    cloud_bottom = min(latest_senkou_a, latest_senkou_b)
    if latest_price > cloud_top and latest_tenkan > latest_kijun:
        signals['Ichimoku Cloud'] = Bullish
        accuracies['Ichimoku Cloud'] = min(95, max(60, int(50 + abs(latest_price - cloud_top) / latest_price * 1000)))
    elif latest_price < cloud_bottom and latest_tenkan < latest_kijun:
        signals['Ichimoku Cloud'] = Bearish
        accuracies['Ichimoku Cloud'] = min(95, max(60, int(50 + abs(cloud_bottom - latest_price) / latest_price * 1000)))
    else:
        signals['Ichimoku Cloud'] = Neutral
        accuracies['Ichimoku Cloud'] = 50

    # Log indicator values and signals
    print("\n=== Indicator Values and Signals ===")
    print(f"RSI: {latest_rsi:.2f} -> Signal: {signals['RSI']} (Accuracy: {accuracies['RSI']}%)")
    print(f"MACD: {latest_macd:.5f}, Signal: {latest_signal:.5f}, Histogram: {latest_histogram:.5f} -> Signal: {signals['MACD']} (Accuracy: {accuracies['MACD']}%)")
    print(f"Bollinger Bands - Upper: {latest_bb_upper:.5f}, Middle: {latest_bb_middle:.5f}, Lower: {latest_bb_lower:.5f} -> Signal: {signals['Bollinger Bands']} (Accuracy: {accuracies['Bollinger Bands']}%)")
    print(f"ADX: {latest_adx:.2f}, +DI: {latest_plus_di:.2f}, -DI: {latest_minus_di:.2f} -> Signal: {signals['ADX']} (Accuracy: {accuracies['ADX']}%)")
    print(f"Stochastic - K: {latest_k:.2f}, D: {latest_d:.2f} -> Signal: {signals['Stochastic']} (Accuracy: {accuracies['Stochastic']}%)")
    print(f"EMA - Fast: {latest_ema_fast:.5f}, Slow: {latest_ema_slow:.5f} -> Signal: {signals['EMA']} (Accuracy: {accuracies['EMA']}%)")
    print(f"ATR: {latest_atr:.5f} (Threshold: {atr_threshold:.5f}) -> Signal: {signals['ATR']} (Accuracy: {accuracies['ATR']}%)")
    print(f"Ichimoku - Tenkan: {latest_tenkan:.5f}, Kijun: {latest_kijun:.5f}, Senkou A: {latest_senkou_a:.5f}, Senkou B: {latest_senkou_b:.5f}, Chikou: {latest_chikou if latest_chikou is not None else 'None'} -> Signal: {signals['Ichimoku Cloud']} (Accuracy: {accuracies['Ichimoku Cloud']}%)")

    # Voting System & SL/TP Calculations
    bullish_count = sum(1 for signal in signals.values() if 'Bullish' in signal)
    bearish_count = sum(1 for signal in signals.values() if 'Bearish' in signal)
    total_signals = len(signals)

    print(f"\nVoting Summary: Bullish: {bullish_count}, Bearish: {bearish_count}, Total: {total_signals}")

    stop_loss = None
    take_profit = None

    if bullish_count > bearish_count:
        final_direction = "🟢 UP 📈"
        accuracy = int(sum(acc for sig, acc in accuracies.items() if 'Bullish' in signals[sig]) / bullish_count) if bullish_count > 0 else 50
        
        # Calculate Long SL & TP
        stop_loss = latest_price - (latest_atr * ATR_SL_MULTIPLIER)
        take_profit = latest_price + (latest_atr * ATR_TP_MULTIPLIER)
        
        print(f"Final Signal: {final_direction} (Accuracy: {accuracy}%)")
        print(f"Entry Price: {latest_price:.5f} | Stop Loss: {stop_loss:.5f} | Take Profit: {take_profit:.5f}")
        
    elif bearish_count > bullish_count:
        final_direction = "🔴 DOWN 📉"
        accuracy = int(sum(acc for sig, acc in accuracies.items() if 'Bearish' in signals[sig]) / bearish_count) if bearish_count > 0 else 50
        
        # Calculate Short SL & TP
        stop_loss = latest_price + (latest_atr * ATR_SL_MULTIPLIER)
        take_profit = latest_price - (latest_atr * ATR_TP_MULTIPLIER)
        
        print(f"Final Signal: {final_direction} (Accuracy: {accuracy}%)")
        print(f"Entry Price: {latest_price:.5f} | Stop Loss: {stop_loss:.5f} | Take Profit: {take_profit:.5f}")
        
    else:
        final_direction = "No clear prediction available"
        accuracy = "N/A"
        print(f"Final Signal: {final_direction} (Accuracy: {accuracy})")

    # Indicator Values
    indicator_values = {
        'RSI': latest_rsi,
        'MACD': latest_macd,
        'MACD_Signal': latest_signal,
        'BB_Upper': latest_bb_upper,
        'BB_Middle': latest_bb_middle,
        'BB_Lower': latest_bb_lower,
        'ADX': latest_adx,
        'Plus_DI': latest_plus_di,
        'Minus_DI': latest_minus_di,
        'Stochastic_K': latest_k,
        'Stochastic_D': latest_d,
        'EMA_Fast': latest_ema_fast,
        'EMA_Slow': latest_ema_slow,
        'ATR': latest_atr,
        'Ichimoku_Tenkan': latest_tenkan,
        'Ichimoku_Kijun': latest_kijun,
        'Ichimoku_Senkou_A': latest_senkou_a,
        'Ichimoku_Senkou_B': latest_senkou_b,
        'Ichimoku_Chikou': latest_chikou
    }

    return {
        "direction": final_direction,
        "accuracy": accuracy,
        "indicator_signals": signals,
        "indicator_values": indicator_values,
        "entry_price": latest_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }

def fetch_data(symbol):
    """Fetch data from Yahoo Finance with retry mechanism."""
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[Attempt {attempt}] Fetching data for {symbol}...")
            df = yf.download(tickers=symbol, interval=INTERVAL, period=PERIOD, auto_adjust=False)

            if df.empty:
                raise ValueError(f"Empty dataframe received for '{symbol}'.")

            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            # df = df.iloc[-DATA_LIMIT:] if len(df) > DATA_LIMIT else df

            # Add timestamp feature (minute of the hour)
            df['timestamp'] = df.index.strftime('%H:%M:%S')

            # Check for data sufficiency
            required_data_points = 100 + 1
            if len(df) < required_data_points:
                raise ValueError(
                    f"Insufficient data: {len(df)} rows fetched for '{symbol}', but {required_data_points} rows are required."
                )

            return df  # Success

        except Exception as e:
            print(f"Error on attempt {attempt} for '{symbol}': {e}")
            last_exception = e
            if attempt < MAX_RETRIES:
                print(f"Retrying in {RETRY_DELAY} seconds...\n")
                time.sleep(RETRY_DELAY)

    # All retries failed
    raise RuntimeError(f"Failed to fetch data for '{symbol}' after {MAX_RETRIES} attempts. Last error: {last_exception}")

def add_features(df):
    """Add timestamp feature and label for direction prediction."""
    df = df.copy()
    
    # Label based on candle color: green (close > open) = 1 (UP), red (close <= open) = 0 (DOWN)
    df["label"] = np.where(df["close"] > df["open"], 1, 0)

    label_counts = df["label"].value_counts()
    label_dist = "\nLabel Distribution (UP/DOWN):\n"
    for label, count in label_counts.items():
        label_dist += f"Label {label}: {count} ({count / len(df) * 100:.2f}%)\n"

    df.dropna(inplace=True)
    return df, label_dist

def get_next_candle_timestamp(current_time, timezone=LOCAL_TIMEZONE):
    """Determine the timestamp of the next 5-minute candle in the specified timezone."""
    # Convert current_time to the specified timezone
    local_tz = pytz.timezone(timezone)
    if current_time.tzinfo is None:
        current_time = pytz.utc.localize(current_time)
    current_time_local = current_time.astimezone(local_tz)
    
    current_minute = current_time_local.minute
    current_hour = current_time_local.hour
    next_5min = (current_minute // 5 + 1) * 5
    if next_5min >= 60:
        next_hour = (current_hour + 1) % 24
        next_5min = next_5min % 60
        return f"{next_hour:02d}:{next_5min:02d}:00"
    return f"{current_hour:02d}:{next_5min:02d}:00"

def plot_candlestick(df, symbol):
    """Plot candlestick chart for the last 60 candles in TradingView dark style with EMA Fast (10) and EMA Slow (20)."""
    df_plot = df.iloc[-60:].copy()

    df_plot['EMA_Fast_10'] = df_plot['close'].ewm(span=10, adjust=False).mean()
    df_plot['EMA_Slow_20'] = df_plot['close'].ewm(span=20, adjust=False).mean()

    mc = mpf.make_marketcolors(
        up='#0faf59',
        down='#ff6251',
        edge='inherit',
        wick='inherit',
        volume='in'
    )

    s = mpf.make_mpf_style(
        base_mpf_style='charles',
        marketcolors=mc,
        facecolor='#0e1117',
        edgecolor='none',
        gridcolor='#1e222d',
        gridstyle='--',
        rc={
            'axes.labelcolor': 'white',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'figure.facecolor': '#0e1117',
            'savefig.facecolor': '#0e1117',
            'savefig.edgecolor': '#0e1117',
        }
    )

    apds = [
        mpf.make_addplot(df_plot['EMA_Fast_10'], color='#00bcd4', width=1.2, label='EMA Fast (10)'),
        mpf.make_addplot(df_plot['EMA_Slow_20'], color='#ff9800', width=1.2, label='EMA Slow (20)')
    ]

    fig, axlist = mpf.plot(
        df_plot,
        type='candle',
        style=s,
        title='',
        ylabel='',
        ylabel_lower='',
        figsize=(12, 8),
        tight_layout=True,
        xrotation=0,
        volume=False,
        addplot=apds,
        returnfig=True
    )

    price_buffer = (df_plot['high'].max() - df_plot['low'].min()) * 0.05
    axlist[0].set_ylim(df_plot['low'].min() - price_buffer, df_plot['high'].max() + price_buffer)

    legend = axlist[0].legend(loc='upper left')
    for text in legend.get_texts():
        text.set_color("white")

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    candlestick_plot = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)

    return candlestick_plot

def predict(symbol, current_time=None, timezone=LOCAL_TIMEZONE):
    """Main trading logic function for web application, using indicator-based prediction."""
    if current_time is None:
        current_time = datetime.now(pytz.utc)
    
    try:
        df = fetch_data(symbol)
        df, label_dist = add_features(df.copy())

        # Generate signal using multiple indicators
        signal_data = generate_signal(df)

        error = None
        if signal_data["direction"] == "No clear prediction available":
            error = f"Currently no signal available for {symbol}. Please try another asset or try again later."

        # impact_time = get_next_candle_timestamp(current_time, timezone)
        impact_time = current_time.astimezone(pytz.timezone(timezone)).strftime('%H:%M:%S')

        # Generate candlestick chart
        candlestick_plot = plot_candlestick(df, symbol)

        return {
            "symbol": symbol,
            "direction": signal_data["direction"],
            "accuracy": signal_data["accuracy"],
            "entry_price": signal_data.get("entry_price"),
            "stop_loss": signal_data.get("stop_loss"),
            "take_profit": signal_data.get("take_profit"),
            "impact_time": impact_time,
            "label_dist": label_dist,
            "candlestick_plot": candlestick_plot,
            "error": error,
            "indicator_signals": signal_data["indicator_signals"],
            "indicator_values": signal_data["indicator_values"]
        }
    except Exception as e:
        return {"error": str(e)}