import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- KONFIGURACJA STRONY ---
st.set_page_config(layout="wide", page_title="Market Intelligence", page_icon="🧠")

# --- ULTRA MODERN PURPLE CSS ---
st.markdown("""
<style>
    /* Ukrycie domyślnych elementów */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Główne tło */
    .stApp {
        background-color: #050505; /* Prawie czarne tło */
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: #E0E0E0;
        font-weight: 300;
        letter-spacing: 1.5px;
    }
    
    /* CUSTOM METRIC CARD */
    .metric-container {
        background-color: #0F0F12;
        border: 1px solid #2D2D35;
        border-left: 3px solid #7C3AED; /* Purple accent */
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        border-color: #8B5CF6;
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.15);
    }
    
    .metric-label {
        font-size: 12px;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 600;
        color: #FFFFFF;
        margin: 5px 0;
    }
    
    .metric-delta-up {
        font-size: 12px;
        color: #7bff00;
        font-weight: 500;
    }
    
    .metric-delta-down {
        font-size: 12px;
        color: #ff0000;
        font-weight: 500;
    }

    /* Alert box */
    .stAlert {
        background-color: #0F0F12;
        border: 1px solid #4C1D95;
        color: #DDD6FE;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNKCJE DANYCH ---
@st.cache_data(ttl=3600)
def get_data_simple():
    tickers_macro = {
        'S&P 500': '^GSPC', 'Nasdaq 100': '^NDX', 'US 10Y Bonds': '^TNX',
        'Gold': 'GC=F', 'Oil (WTI)': 'CL=F', 'VIX': '^VIX', 'USD Index': 'DX-Y.NYB'
    }
    sectors = {
        'Technology': 'XLK', 'Financials': 'XLF', 'Healthcare': 'XLV',
        'Energy': 'XLE', 'Discretionary': 'XLY', 'Staples': 'XLP',
        'Utilities': 'XLU', 'Real Estate': 'XLRE'
    }

    def fetch_clean(ticker_dict):
        symbols = list(ticker_dict.values())
        raw_data = yf.download(symbols, period="1y", auto_adjust=False, progress=False)
        
        if 'Close' in raw_data.columns:
            df = raw_data['Close']
        else:
            df = raw_data
            
        inv_map = {v: k for k, v in ticker_dict.items()}
        valid_cols = [c for c in df.columns if c in inv_map]
        df = df[valid_cols]
        df.columns = [inv_map[c] for c in df.columns]
        return df.ffill().dropna()

    try:
        df_macro = fetch_clean(tickers_macro)
        df_sectors = fetch_clean(sectors)
        return df_macro, df_sectors
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

# --- HELPER: CUSTOM METRIC HTML ---
def custom_metric(label, value, delta):
    delta_val = float(delta.strip('%'))
    delta_class = "metric-delta-up" if delta_val >= 0 else "metric-delta-down"
    # Strzałka w górę lub tylko minus
    icon = "▲" if delta_val >= 0 else "▼"
    
    html = f"""
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="{delta_class}">{icon} {delta}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- LOGIKA APLIKACJI ---

st.title("🧠 Market Intelligence")
st.caption("Automated Quantitative Analysis System")
st.markdown("---")

df_macro, df_sectors = get_data_simple()

if not df_macro.empty and not df_sectors.empty:
    
    # 1. KPI SNAPSHOT (Custom HTML)
    daily_change = df_macro.pct_change().iloc[-1] * 100
    last_prices = df_macro.iloc[-1]
    
    # Grid metryk (Responsywny)
    cols = st.columns(4)
    keys = list(df_macro.columns)
    
    # Pierwszy rząd
    for i in range(4):
        if i < len(keys):
            name = keys[i]
            with cols[i]:
                custom_metric(name, f"{last_prices[name]:,.2f}", f"{daily_change[name]:.2f}%")
    
    # Drugi rząd
    cols2 = st.columns(4)
    for i in range(4, len(keys)):
        name = keys[i]
        with cols2[i-4]:
            custom_metric(name, f"{last_prices[name]:,.2f}", f"{daily_change[name]:.2f}%")

    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    # 2. SEKTORY (Modern Purple Bars)
    with col1:
        st.subheader("Sector Momentum (YTD)")
        start_price = df_sectors.iloc[0]
        end_price = df_sectors.iloc[-1]
        ytd_perf = ((end_price - start_price) / start_price * 100).sort_values(ascending=True)
        
        fig_sec = px.bar(
            x=ytd_perf.values, 
            y=ytd_perf.index, 
            orientation='h',
            text_auto='.1f',
            template="plotly_dark",
            # Skala: Grafit -> Fiolet
            color=ytd_perf.values,
            color_continuous_scale=['#27272a', '#5b21b6', '#8b5cf6', '#a78bfa'] 
        )
        fig_sec.update_layout(
            xaxis_title=None, yaxis_title=None, showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=350,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False),
            coloraxis_showscale=False,
            font=dict(family="Inter, sans-serif", size=12)
        )
        fig_sec.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_sec, use_container_width=True)

    # 3. ROLLING CORRELATION (Zamiast Matrycy)
    with col2:
        st.subheader("Dynamic Correlation vs S&P 500")
        
        # Obliczanie korelacji ruchomej (Rolling 30-day window)
        # Porównujemy wszystko do S&P 500
        benchmark = df_macro['S&P 500'].pct_change()
        assets = ['US 10Y Bonds', 'VIX', 'Gold', 'USD Index']
        
        rolling_corr_df = pd.DataFrame()
        for asset in assets:
            rolling_corr_df[asset] = df_macro[asset].pct_change().rolling(window=30).corr(benchmark)
            
        # Wykres liniowy
        fig_roll = px.line(
            rolling_corr_df.tail(180), # Ostatnie pół roku
            template="plotly_dark",
            color_discrete_sequence=["#ff00ff", "#ff0000", "#ffcc00", "#0062ff"] # Fiolet, Czerwony, Złoty, Niebieski
        )
        fig_roll.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=350,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#333', zeroline=True, zerolinecolor='#666'),
            legend=dict(orientation="h", y=1.1, x=0),
            font=dict(family="Inter, sans-serif", size=11)
        )
        st.plotly_chart(fig_roll, use_container_width=True)

    # 4. INSIGHTS
    st.markdown("---")
    
    # Prosta analiza
    bond_yield = last_prices['US 10Y Bonds']
    market_state = "RISK-ON" if daily_change['S&P 500'] > 0 else "RISK-OFF"
    
    st.info(f"""
    **🤖 AUTOMATED INSIGHTS:**
    
    * **Regime:** `{market_state}` detected.
    * **Capital Flow:** Leading sector is **{ytd_perf.index[-1]}** (+{ytd_perf.iloc[-1]:.1f}%).
    * **Correlation Watch:** Check **VIX** i **S&P 500** on chart above.
    """)

else:
    st.warning("⚠️ Brak danych. Sprawdź połączenie z internetem.")