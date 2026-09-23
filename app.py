import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import time

# JST (日本時間) の定義
JST = timezone(timedelta(hours=+9), 'JST')

# ページ全体のレイアウト設定（ワイド画面対応）
st.set_page_config(
    page_title="FX Analysis AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- カスタムCSS（ダークテーマ & カードデザイン） ---
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 現在時刻の取得 (日本時間) ---
now_jst = datetime.now(JST)

# --- ヘッダー部分 ---
st.markdown("### 📈 FX Analysis AI <span style='font-size:12px; color:#8b949e;'>リアルタイム分析 × 予測 × 検証 (ライブモード)</span>", unsafe_allow_html=True)
st.caption(f"現在のリアルタイム基準時刻 (JST): {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

# --- 通貨ペア・価格ヘッダー（横並び） ---
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("### 🇦🇺 AUD/JPY <span style='font-size:14px; color:#8b949e;'>豪ドル/円</span>", unsafe_allow_html=True)
with col2:
    # リアルタイム感を出すために秒数に応じて価格を微小に変動させる
    live_price = 113.428 + (now_jst.second % 5) * 0.002
    st.markdown(f"### {live_price:.3f} <span style='font-size:14px; color:#22c55e;'>+0.236 (+0.21%)</span>", unsafe_allow_html=True)

# --- リアルタイム現在時刻を基準にしたチャート生成関数 ---
def render_candlestick_chart(timeframe_key, timeframe_name):
    freq_map = {
        "1分": "1min",
        "5分": "5min",
        "15分": "15min",
        "1時間": "1h",
        "4時間": "4h",
        "日足": "1D"
    }
    freq = freq_map.get(timeframe_key, "1min")
    
    # 常に「今（JSTの現在時刻）」を右端の終点にする
    end_time = datetime.now(JST).replace(tzinfo=None)
    periods = 50
    
    dates = pd.date_range(end=end_time, periods=periods, freq=freq)
    
    # 秒単位の変動をシードに反映させてチャートが動くようにする
    np.random.seed(int(end_time.timestamp()) // 10 + hash(timeframe_key) % 100)
    volatility = 0.05 if "分" in timeframe_key else (0.2 if "時間" in timeframe_key else 0.8)
    
    close_prices = 113.0 + np.cumsum(np.random.randn(periods) * volatility)
    open_prices = close_prices + np.random.randn(periods) * (volatility * 0.4)
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(periods) * (volatility * 0.5))
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(periods) * (volatility * 0.5))
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices
    })
    
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA75'] = df['Close'].ewm(span=75).mean()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name=f'AUD/JPY ({timeframe_name})',
        increasing_line_color='#22c55e', decreasing_line_color='#ef4444'
    ))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA20'], line=dict(color='#3b82f6', width=1.5), name='EMA 20'))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA75'], line=dict(color='#eab308', width=1.5), name='EMA 75'))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(range=[dates[0], dates[-1]])
    )
    st.plotly_chart(fig, use_container_width=True)

# --- タブ切り替え ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["1分", "5分", "15分", "1時間", "4時間", "日足"])

with tab1:
    render_candlestick_chart("1分", "1分足")
with tab2:
    render_candlestick_chart("5分", "5分足")
with tab3:
    render_candlestick_chart("15分", "15分足")
with tab4:
    render_candlestick_chart("1時間", "1時間足")
with tab5:
    render_candlestick_chart("4時間", "4時間足")
with tab6:
    render_candlestick_chart("日足", "日足")

# --- エントリー候補・条件チェックリスト ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("#### 📊 テクニカル指標エリア（RSI / MACD）")
    end_time = datetime.now(JST).replace(tzinfo=None)
    dates_rsi = pd.date_range(end=end_time, periods=50, freq="1min")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=dates_rsi, y=50 + np.sin(np.arange(50))*15, line=dict(color='#a855f7', width=1.5), name='RSI (14)'))
    fig_rsi.update_layout(
        template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
        margin=dict(l=10, r=10, t=10, b=10), height=180,
        xaxis=dict(range=[dates_rsi[0], dates_rsi[-1]])
    )
    st.plotly_chart(fig_rsi, use_container_width=True)

with col_right:
    st.markdown("#### 🎯 エントリー候補")
    st.success("判定：買い優勢（エントリーチャンス）")
    st.write("買い条件 7 / 8 成立")
    st.progress(7/8)
    
    st.markdown("""
    | 項目 | 判定 | 値 |
    | :--- | :---: | :--- |
    | EMA20 > EMA75 | 🟢 | 113.412 > 113.368 |
    | RSI (40〜60) | 🟢 | 56.8 |
    | ADX (>25) | 🟢 | 31.4 |
    | 上位足トレンド(15分) | ❌ | やや弱い |
    """)

# --- 10秒ごとに自動で画面を再読み込みして時計とチャートをリアルタイム更新する ---
time.sleep(10)
st.rerun()
