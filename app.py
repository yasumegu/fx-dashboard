import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. ページ全体の基本設定（ワイド表示 ＆ ダーク風）
st.set_page_config(
    page_title="FX Analysis AI",
    page_icon="📈",
    layout="wide"
)

# 2. サイドバー：パラメーター設定パネル
st.sidebar.header("⚙️ パラメーター設定")

currency_map = {
    "USD/JPY": "USDJPY=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X"
}
selected_name = st.sidebar.selectbox("通貨ペア", list(currency_map.keys()))
ticker_symbol = currency_map[selected_name]

# 時間足の選択肢を拡充（1m, 5m, 15m, 30m, 1h, 1d）
interval = st.sidebar.selectbox("時間足", ["1m", "5m", "15m", "30m", "1h", "1d"], index=4)
period = st.sidebar.selectbox("取得期間", ["1d", "5d", "1mo", "3mo"], index=1)

st.sidebar.markdown("---")
st.sidebar.subheader("インジケーター設定")
ema_short = st.sidebar.number_input("短期EMA 期間", value=20)
ema_long = st.sidebar.number_input("長期EMA 期間", value=75)
rsi_period = st.sidebar.number_input("RSI 期間", value=14)
adx_period = st.sidebar.number_input("ADX 期間", value=14)

st.sidebar.markdown("---")
st.sidebar.subheader("📧 メール通知設定")
enable_email = st.sidebar.checkbox("メール通知を有効化", value=False)
sender_email = st.sidebar.text_input("送信元 Gmailアドレス", placeholder="your_email@gmail.com")
email_password = st.sidebar.text_input("Gmail アプリパスワード", type="password", placeholder="16桁のアプリパスワード")
target_email = "yasutaka.meguri@gmail.com"

# 3. メインヘッダー
st.markdown(f"## 📈 FX Analysis AI <span style='font-size:16px; color:#00FF7F;'>● Live: {selected_name} ({interval})</span>", unsafe_allow_html=True)
st.markdown("---")

# 4. リアルタイムデータの取得
@st.cache_data(ttl=30)
def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

data = load_data(ticker_symbol, period, interval)

if data.empty or len(data) < max(ema_long, rsi_period, adx_period) + 2:
    st.error("データが不足しているか、選択した時間足に対して期間が不正です（例：1m足は7日以内のみ取得可能）。期間を調整してください。")
else:
    # --- テクニカル指標の計算 ---
    data['EMA_Short'] = data['Close'].ewm(span=ema_short, adjust=False).mean()
    data['EMA_Long'] = data['Close'].ewm(span=ema_long, adjust=False).mean()
    
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']

    high = data['High']
    low = data['Low']
    close = data['Close']
    
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)
    
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=adx_period).mean()
    
    plus_di = 100 * pd.Series(plus_dm, index=data.index).rolling(window=adx_period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=data.index).rolling(window=adx_period).mean() / atr
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di)).fillna(0)
    data['ADX'] = dx.rolling(window=adx_period).mean()

    latest = data.iloc[-1]
    prev = data.iloc[-2]
    change = latest['Close'] - prev['Close']
    pct_change = (change / prev['Close']) * 100

    # --- 5. 上段：現在値 & インジケーターカード ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("現在値 (Close)", f"{latest['Close']:.3f}", f"{change:+.3f} ({pct_change:+.2f}%)")
    with col2:
        st.metric(f"短期EMA ({ema_short})", f"{latest['EMA_Short']:.3f}")
    with col3:
        st.metric(f"長期EMA ({ema_long})", f"{latest['EMA_Long']:.3f}")
    with col4:
        st.metric(f"RSI ({rsi_period})", f"{latest['RSI']:.1f}")
    with col5:
        st.metric("ADX", f"{latest['ADX']:.1f}" if not np.isnan(latest['ADX']) else "計算中")

    # --- 6. メインレイアウト（左：マルチチャート / 右：予測感知・勝率スコア） ---
    left_col, right_col = st.columns([7, 4])

    with left_col:
        st.subheader("📊 マルチテクニカル分析チャート")
        
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
        
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name="ローソク足", increasing_line_color='#00FF7F', decreasing_line_color='#FF4500'
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_Short'], line=dict(color='#FFA500', width=1), name=f'EMA {ema_short}'), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_Long'], line=dict(color='#00FFFF', width=1), name=f'EMA {ema_long}'), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='#00FFFF', width=1), name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], line=dict(color='#FF00FF', width=1), name='Signal'), row=2, col=1)
        fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color='gray', name='Hist'), row=2, col=1)
        
        fig.add_trace(go.Scatter(x=data.index, y=data['ADX'], line=dict(color='#FFFF00', width=1.5), name='ADX'), row=3, col=1)

        fig.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=10, t=10, b=10),
            height=550,
            xaxis_rangeslider_visible=False,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("🎯 予測感知 & 勝率スコア")
        
        buy_score = 0
        total_conditions = 4
        
        c1 = latest['EMA_Short'] > latest['EMA_Long']
        if c1: buy_score += 1
        
        c2 = 40 <= latest['RSI'] <= 65
        if c2: buy_score += 1
        
        c3 = latest['MACD'] > latest['MACD_Signal']
        if c3: buy_score += 1
        
        adx_val = latest['ADX'] if not np.isnan(latest['ADX']) else 0
        c4 = adx_val > 20
        if c4: buy_score += 1

        buy_probability = int((buy_score / total_conditions) * 100)

        if buy_score >= 3:
            st.markdown("🟢 **判定：強い買い優勢（エントリーチャンス）**")
            signal_status = "買いシグナル発動"
        elif buy_score <= 1:
            st.markdown("🔴 **判定：強い売り優勢**")
            signal_status = "売りシグナル発動"
        else:
            st.markdown("🟡 **判定：レンジ・様子見推奨**")
            signal_status = "様子見"

        st.markdown(f"**AI予測勝率（買い方向）: {buy_probability}%**")
        st.progress(buy_probability / 100)

        # メール送信処理（修正箇所: enable_alert -> enable_email）
        if 'last_alert_time' not in st.session_state:
            st.session_state.last_alert_time = ""

        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        if enable_email and buy_score >= 3 and st.session_state.last_alert_time != current_time_str:
            if sender_email and email_password:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = target_email
                    msg['Subject'] = f"【FX Alert】{selected_name} ({interval}) 買いシグナル検知！"
                    body = f"高勝率シグナルを検知しました。\n\n通貨ペア: {selected_name}\n時間足: {interval}\n価格: {latest['Close']:.3f}\n予測勝率: {buy_probability}%\n時刻: {current_time_str}"
                    msg.attach(MIMEText(body, 'plain'))
                    
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, email_password)
                    server.sendmail(sender_email, target_email, msg.as_string())
                    server.quit()
                    
                    st.success(f"📧 {target_email} へ通知メールを送信しました！")
                    st.session_state.last_alert_time = current_time_str
                except Exception as e:
                    st.error(f"メール送信エラー: {e}")
            else:
                st.warning("⚠️ メール通知が有効ですが、送信元アドレスまたはアプリパスワードが入力されていません。")

        st.markdown("#### 📋 条件チェックリスト")
        checklist_df = pd.DataFrame({
            "評価項目": [
                f"EMA ({ema_short}) > EMA ({ema_long})", 
                f"RSI ({rsi_period}) 正常域 (40〜65)", 
                "MACD > シグナル", 
                "ADX トレンド強度 (>20)"
            ],
            "状態": [
                "✅ 成立" if c1 else "❌ 不成立",
                "✅ 成立" if c2 else "❌ 不成立",
                "✅ 成立" if c3 else "❌ 不成立",
                "✅ 成立" if c4 else "❌ 不成立"
            ],
            "現在値": [
                f"{latest['EMA_Short']:.2f} > {latest['EMA_Long']:.2f}",
                f"{latest['RSI']:.1f}",
                f"{latest['MACD']:.3f} > {latest['MACD_Signal']:.3f}",
                f"{adx_val:.1f}"
            ]
        })
        st.table(checklist_df)

# --- 7. 下段：シグナル履歴ログ ---
st.markdown("---")
st.subheader("📜 リアルタイム・シグナル履歴ログ")

if 'history' not in st.session_state:
    st.session_state.history = []

timestamp_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if not st.session_state.history or st.session_state.history[0]['時刻'] != timestamp_display[:16]:
    st.session_state.history.insert(0, {
        "時刻": timestamp_display,
        "通貨ペア": selected_name,
        "時間足": interval,
        "判定": signal_status,
        "予測勝率": f"{buy_probability}%",
        "価格": f"{latest['Close']:.3f}"
    })
    if len(st.session_state.history) > 10:
        st.session_state.history.pop()

history_df = pd.DataFrame(st.session_state.history)
st.dataframe(history_df, use_container_width=True)

# フッター
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>FX Analysis AI Dashboard — Multi-Timeframe & Email Alert Integrated</p>", unsafe_allow_html=True)