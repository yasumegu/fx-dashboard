import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import time

# JST (日本時間) の定義
JST = timezone(timedelta(hours=+9), 'JST')

# ページ全体のレイアウト設定（スマホアプリ風のコンパクトかつダークなデザイン）
st.set_page_config(
    page_title="FX Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- カスタムCSS（ダークテーマ & FXトレード画面風スタイル） ---
st.markdown("""
<style>
    .main {
        background-color: #0c0f17;
        color: #e6e6e6;
    }
    .stApp {
        background-color: #0c0f17;
    }
    .bid-box {
        background: linear-gradient(135deg, #16222a 0%, #1a365d 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    .ask-box {
        background: linear-gradient(135deg, #2a1619 0%, #5d1a21 100%);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    .panel-box {
        background-color: #131822;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 現在時刻の取得 (日本時間) ---
now_jst = datetime.now(JST)

# --- レートおよびスプレッドのリアルタイム変動計算 ---
# 秒数や分数を活用して、Bid/Ask、スプレッドがリアルタイムに変動するように設定
np.random.seed(int(now_jst.timestamp()) // 5)
base_price = 111.415 + (now_jst.minute % 10) * 0.002
bid_val = base_price + (now_jst.second % 3) * 0.001
# スプレッドをリアルタイムに変動させる（例: 4.5 〜 6.8 pipsの間でライブ変動）
spread_val = 4.5 + (now_jst.second % 5) * 0.4 + (now_jst.microsecond % 10) * 0.05
ask_val = bid_val + (spread_val * 0.01)

# --- ヘッダー部分 ---
header_col1, header_col2, header_col3 = st.columns([1, 2, 1])
with header_col1:
    st.markdown("### ≡ <span style='font-size:15px;'>チャート</span>", unsafe_allow_html=True)
with header_col2:
    st.markdown(f"<div style='text-align:center; font-size:12px; color:#8b949e;'><b>AUD/JPY</b> {now_jst.strftime('%y/%m/%d %H:%M')}<br><b>O</b> {base_price:.3f} <b>H</b> {ask_val:.3f} <b>C</b> {bid_val:.3f} <b>L</b> {base_price-0.005:.3f}</div>", unsafe_allow_html=True)
with header_col3:
    st.markdown("<div style='text-align:right; font-size:16px;'>⚙️ 🔲</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 4px 0px; border-color: #21262d;'>", unsafe_allow_html=True)

# --- タイムフレーム選択タブ ---
tf_cols = st.columns(6)
timeframe = "1分"
with tf_cols[0]:
    if st.button("1分", use_container_width=True): timeframe = "1分"
with tf_cols[1]:
    if st.button("5分", use_container_width=True): timeframe = "5分"
with tf_cols[2]:
    if st.button("15分", use_container_width=True): timeframe = "15分"
with tf_cols[3]:
    if st.button("1時間", use_container_width=True): timeframe = "1時間"
with tf_cols[4]:
    if st.button("4時間", use_container_width=True): timeframe = "4時間"
with tf_cols[5]:
    if st.button("日足", use_container_width=True): timeframe = "日足"

# --- 高機能サブプロットチャート（ローソク足 ＋ ボリンジャーバンド ＋ MACD ＋ RSI） ---
def render_pro_charts():
    periods = 60
    dates = pd.date_range(end=now_jst.replace(tzinfo=None), periods=periods, freq="1min")
    
    volatility = 0.04
    close_prices = 111.35 + np.cumsum(np.random.randn(periods) * volatility)
    open_prices = close_prices + np.random.randn(periods) * (volatility * 0.4)
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(periods) * (volatility * 0.5))
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(periods) * (volatility * 0.5))
    
    df = pd.DataFrame({'Date': dates, 'Open': open_prices, 'High': high_prices, 'Low': low_prices, 'Close': close_prices})
    
    # ボリンジャーバンド計算 (期間10)
    df['MA10'] = df['Close'].rolling(10).mean()
    df['STD10'] = df['Close'].rolling(10).std()
    df['BB_UP1'] = df['MA10'] + 1 * df['STD10']
    df['BB_DN1'] = df['MA10'] - 1 * df['STD10']
    df['BB_UP2'] = df['MA10'] + 2 * df['STD10']
    df['BB_DN2'] = df['MA10'] - 2 * df['STD10']
    df['BB_UP3'] = df['MA10'] + 3 * df['STD10']
    df['BB_DN3'] = df['MA10'] - 3 * df['STD10']
    
    # MACD計算
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=10, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    # RSI計算
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 3段サブプロット (ローソク+BB / MACD / RSI)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.55, 0.22, 0.23])

    # 1. ローソク足 & ボリンジャーバンド
    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='AUD/JPY', increasing_line_color='#22c55e', decreasing_line_color='#ef4444'
    ), row=1, col=1)
    
    for col_name, color in [('BB_UP3', '#8b5cf6'), ('BB_UP2', '#3b82f6'), ('BB_UP1', '#06b6d4'),
                            ('BB_DN1', '#06b6d4'), ('BB_DN2', '#3b82f6'), ('BB_DN3', '#8b5cf6')]:
        fig.add_trace(go.Scatter(x=df['Date'], y=df[col_name], line=dict(color=color, width=1), showlegend=False), row=1, col=1)

    # 2. MACD
    fig.add_trace(go.Bar(x=df['Date'], y=df['Hist'], marker_color=np.where(df['Hist']>=0, '#22c55e', '#ef4444'), name='Hist'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], line=dict(color='#ef4444', width=1.2), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], line=dict(color='#3b82f6', width=1.2), name='Signal'), row=2, col=1)

    # 3. RSI
    fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], line=dict(color='#eab308', width=1.5), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="#555555", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#3b82f6", row=3, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0c0f17',
        plot_bgcolor='#0c0f17',
        margin=dict(l=5, r=5, t=5, b=5),
        height=420,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

render_pro_charts()

# --- 下部トレード・レート発注パネル ---
col_bid, col_spread, col_ask = st.columns([1.2, 0.6, 1.2])

with col_bid:
    st.markdown(f"""
    <div class="bid-box">
        <div style="font-size: 10px; color: #93c5fd;">Bid / 売</div>
        <div style="font-size: 22px; font-weight: bold; color: #ffffff;">{bid_val:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_spread:
    st.markdown(f"""
    <div style="text-align: center; padding-top: 6px;">
        <span style="background-color: #1e293b; border-radius: 50%; padding: 4px 8px; font-size: 11px; color: #facc15;">{spread_val:.1f}</span>
        <div style="font-size: 9px; color: #8b949e; margin-top: 2px;">スプレッド</div>
    </div>
    """, unsafe_allow_html=True)

with col_ask:
    st.markdown(f"""
    <div class="ask-box">
        <div style="font-size: 10px; color: #fca5a5;">Ask / 買</div>
        <div style="font-size: 22px; font-weight: bold; color: #ffffff;">{ask_val:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 口座状況・Lot数・一括決済パネル ---
st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
p_col1, p_col2, p_col3 = st.columns(3)

with p_col1:
    st.markdown("<span style='font-size:10px; color:#8b949e;'>純資産額</span><br><b style='font-size:13px;'>98,481 円</b>", unsafe_allow_html=True)
with p_col2:
    st.markdown("<span style='font-size:10px; color:#8b949e;'>数量 (Lot)</span><br><b style='font-size:13px;'>23 (<span style='color:#ef4444;'>-4,669円</span>)</b>", unsafe_allow_html=True)
with p_col3:
    st.toggle("一括決済", value=False, key="batch_close")

st.markdown("</div>", unsafe_allow_html=True)

# --- 判定・エントリー条件チェックリストセクション ---
st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
st.markdown("#### 🎯 エントリー候補・条件判定", unsafe_allow_html=True)
st.success("判定：買い優勢（エントリーチャンス）")
st.write("買い条件 7 / 8 成立")
st.progress(7/8)

st.markdown(f"""
| 項目 | 判定 | 値 / 状態 |
| :--- | :---: | :--- |
| EMA20 > EMA75 | 🟢 | 113.412 > 113.368 |
| RSI (40〜60) | 🟢 | 56.8 (中立) |
| MACDゴールデンクロス | 🟢 | 成立中 |
| ボリンジャーバンド下限反発 | 🟢 | -1σタッチ |
| ADX (トレンド強度) | 🟢 | 31.4 (>25) |
| 上位足トレンド(15分) | ❌ | やや弱い |
| スプレッド条件 | 🟢 | {spread_val:.1f} pips (基準値内) |
""")
st.markdown("</div>", unsafe_allow_html=True)

# --- フッター（最終更新時刻） ---
st.markdown(f"<div style='text-align: right; font-size: 10px; color: #8b949e;'>Updated {now_jst.strftime('%Y/%m/%d %H:%M:%S')}</div>", unsafe_allow_html=True)

# --- 5秒ごとに自動で画面を再読み込みしてリアルタイムに動かす ---
time.sleep(5)
st.rerun()
