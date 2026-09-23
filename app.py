import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

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

# --- ヘッダー部分 ---
st.markdown("### 📈 FX Analysis AI <span style='font-size:12px; color:#8b949e;'>リアルタイム分析 × 予測 × 検証</span>", unsafe_allow_html=True)

# --- 通貨ペア・価格ヘッダー（横並び） ---
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("### 🇦🇺 AUD/JPY <span style='font-size:14px; color:#8b949e;'>豪ドル/円</span>", unsafe_allow_html=True)
with col2:
    st.markdown("### 113.428 <span style='font-size:14px; color:#22c55e;'>+0.236 (+0.21%)</span>", unsafe_allow_html=True)

# --- タブ切り替え ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["1分", "5分", "15分", "1時間", "4時間", "日足"])

with tab1:
    # --- サンプルデータの生成（ローソク足・インジケーター用） ---
    np.random.seed(42)
    dates = pd.date_range(start="2026-09-24 09:00", periods=50, freq="1min")
    close_prices = 113.0 + np.cumsum(np.random.randn(50) * 0.05)
    open_prices = close_prices + np.random.randn(50) * 0.02
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(50) * 0.03)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(50) * 0.03)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices
    })
    
    # 移動平均線の計算
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA75'] = df['Close'].ewm(span=75).mean()

    # --- Plotlyによるローソク足チャートの作成 ---
    fig = go.Figure()

    # ローソク足
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='AUD/JPY',
        increasing_line_color='#22c55e', decreasing_line_color='#ef4444'
    ))

    # EMA20
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['EMA20'],
        line=dict(color='#3b82f6', width=1.5),
        name='EMA 20'
    ))

    # EMA75
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['EMA75'],
        line=dict(color='#eab308', width=1.5),
        name='EMA 75'
    ))

    # グラフのダークモードデザイン調整
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

# --- エントリー候補・条件チェックリスト ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("#### 📊 テクニカル指標エリア（RSI / MACD）")
    # RSI風のダミーサブチャート
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=dates, y=50 + np.sin(np.arange(50))*15, line=dict(color='#a855f7', width=1.5), name='RSI (14)'))
    fig_rsi.update_layout(
        template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
        margin=dict(l=10, r=10, t=10, b=10), height=180
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
