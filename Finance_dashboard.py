import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
import time

st.set_page_config(page_title="Finance Dashboard", page_icon="💰", layout="wide")
st.title("💰 Finance — Real-Time Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

@st.cache_data(ttl=1800)
def get_stocks():
    try:
        import yfinance as yf
        import time
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META"]
        data = {}
        for s in symbols:
            try:
                ticker = yf.Ticker(s)
                hist = ticker.history(period="30d", interval="1d")
                if not hist.empty:
                    data[s] = hist
                time.sleep(1)
            except:
                pass
        return data
    except Exception as e:
        st.error(f"Error: {e}")
        return {}

@st.cache_data(ttl=1800)
def get_crypto():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin,ethereum,binancecoin,solana",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            },
            timeout=30
        ).json()
        return r
    except:
        return {}

with st.sidebar:
    st.header("⚙️ Settings")
    refresh = st.selectbox("Auto-Refresh (minutes)", [5, 15, 30, 60], index=2)
    section = st.radio("View", ["Stocks", "Crypto", "Both"])
    st.caption("Data: Yahoo Finance + CoinGecko")

with st.spinner("Fetching live data..."):
    stocks = get_stocks()
    crypto = get_crypto()

st.divider()

if section in ["Stocks", "Both"]:
    st.subheader("📈 Stock Prices")
    if stocks:
        cols = st.columns(len(stocks))
        for i, (sym, df) in enumerate(stocks.items()):
            price = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2] if len(df) > 1 else price
            delta = ((price - prev) / prev) * 100
            cols[i].metric(sym, f"${price:.2f}", f"{delta:+.2f}%")

        st.divider()

        st.subheader("📊 30-Day Trend")
        selected = st.radio("Select stock", list(stocks.keys()), horizontal=True)
        df = stocks[selected]
        daily = df["Close"].reset_index()
        daily.columns = ["Date", "Price"]
        color = "#00e5a0" if daily["Price"].iloc[-1] >= daily["Price"].iloc[0] else "#ff4d6d"
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["Date"], y=daily["Price"],
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(0,229,160,0.08)",
            name=selected,
            hovertemplate="<b>%{x|%b %d}</b><br>$%{y:.2f}<extra></extra>",
        ))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis=dict(tickprefix="$"))
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("🌊 30-Day Volatility")
        vol_data = []
        for sym, df in stocks.items():
            vol = df["Close"].pct_change().std() * 100
            vol_data.append({"Symbol": sym, "Volatility (%)": round(vol, 2)})
        vol_df = pd.DataFrame(vol_data)
        st.bar_chart(vol_df.set_index("Symbol"))

    else:
        st.warning("Stock data unavailable")

st.divider()

if section in ["Crypto", "Both"]:
    st.subheader("🪙 Crypto Prices (USD)")
    if crypto:
        names = {
            "bitcoin": "Bitcoin (BTC)",
            "ethereum": "Ethereum (ETH)",
            "binancecoin": "BNB",
            "solana": "Solana (SOL)"
        }
        cols = st.columns(len(crypto))
        for i, (coin, val) in enumerate(crypto.items()):
            price = val.get("usd", 0)
            change = val.get("usd_24h_change", 0)
            cols[i].metric(
                names.get(coin, coin),
                f"${price:,.2f}",
                f"{change:+.2f}%"
            )
    else:
        st.warning("Crypto data unavailable")

st.divider()
st.caption(f"⏱ Auto-refreshes every {refresh} minutes.")

if "last_run" not in st.session_state:
    st.session_state["last_run"] = time.time()
if time.time() - st.session_state["last_run"] >= refresh * 60:
    st.session_state["last_run"] = time.time()
    st.rerun()
    