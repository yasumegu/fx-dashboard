import streamlit as st

# ページ全体のレイアウト設定（ワイド画面対応）
st.set_page_config(
    page_title="FX Analysis AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- カスタムCSS（見た目をダーク & リッチに調整） ---
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
    st.info("ここに1分足のチャートやインジケーターが表示されます")

# --- エントリー候補・条件チェックリスト ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("#### 📊 テクニカル指標エリア")
    st.write("RSI, MACD, ADX などの詳細データ")

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
