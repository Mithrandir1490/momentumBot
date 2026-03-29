import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Momentum Strategy Bot", layout="wide")

st.title("🚀 Momentum Strategy Bot v1.7")
st.sidebar.header("Configuración de Estrategia")

# --- PARÁMETROS EN SIDEBAR ---
capital_total = st.sidebar.number_input("Capital Disponible (USD)", value=50000)
stop_loss = st.sidebar.slider("Stop Loss (%)", 1, 10, 4) / 100
take_profit = st.sidebar.slider("Take Profit (%)", 1, 20, 8) / 100
umbral_r2 = st.sidebar.slider("Umbral R2 (Calidad)", 0.5, 0.9, 0.8)

# LISTA DE TICKERS (Puedes editarla aquí)
TICKERS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "GEV", "VST", "CEG", "CCJ", "COIN", "MSTR", "LLY", "AVAV", "WMT", "JPM", "GS", "PLTR", "SMR", "OKLO"]

# --- MOTOR DE ANÁLISIS ---
def analizar_ticker(ticker):
    try:
        raw = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if raw.empty: return None
        if isinstance(raw.columns, pd.MultiIndex): data = raw['Close'][ticker]
        else: data = raw['Close']
        data = data.squeeze().dropna()
        if len(data) < 90: return None
        
        serie = data.tail(90)
        log_prices = np.log(serie)
        slope, _, r_val, _, _ = linregress(np.arange(len(log_prices)), log_prices.values)
        
        return {
            "Ticker": ticker,
            "Precio": round(data.iloc[-1], 2),
            "Momentum_Anual": round((np.exp(slope) ** 252) - 1, 4),
            "R2": round(r_val**2, 4),
            "Sobre_MA20": data.iloc[-1] > data.rolling(20).mean().iloc[-1]
        }
    except: return None

# --- INTERFAZ DE USUARIO (TABS) ---
tab1, tab2 = st.tabs(["🔍 Escáner de Mercado", "📊 Mi Portafolio"])

with tab1:
    if st.button("🚀 Ejecutar Escaneo de Lunes"):
        with st.spinner("Analizando inercia en el mercado..."):
            resultados = []
            for t in TICKERS:
                res = analizar_ticker(t)
                if res: resultados.append(res)
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # GANADORES
                st.subheader("✅ Señales de Compra (Alta Convicción)")
                df_ganadores = df[(df['R2'] >= umbral_r2) & (df['Sobre_MA20'] == True)]
                if not df_ganadores.empty:
                    df_ganadores = df_ganadores.sort_values(by="Momentum_Anual", ascending=False).head(5)
                    df_ganadores['Inversión_USD'] = (df_ganadores['R2'] / df_ganadores['R2'].sum()) * capital_total
                    df_ganadores['Acciones'] = (df_ganadores['Inversión_USD'] / df_ganadores['Precio']).apply(np.floor)
                    st.dataframe(df_ganadores[['Ticker', 'Momentum_Anual', 'R2', 'Inversión_USD', 'Acciones']], use_container_width=True)
                else:
                    st.warning("No hay señales de alta calidad hoy. Mejor esperar.")

                # WATCHLIST
                st.subheader("🔭 Candidatos en Observación")
                df_watch = df.sort_values(by="Momentum_Anual", ascending=False).head(10)
                st.table(df_watch[['Ticker', 'Momentum_Anual', 'R2', 'Sobre_MA20']])
            else:
                st.error("No se pudieron obtener datos. Intenta de nuevo en unos minutos.")

with tab2:
    st.header("Seguimiento de Posiciones")
    # Nota: Streamlit Cloud no guarda archivos CSV permanentemente sin base de datos.
    # Por ahora, usaremos un "Data Editor" manual para tus compras.
    if 'mis_trades' not in st.session_state:
        st.session_state.mis_trades = pd.DataFrame(columns=["Ticker", "Precio_Entrada", "Fecha"])

    st.write("Registra tus compras aquí:")
    edited_df = st.data_editor(st.session_state.mis_trades, num_rows="dynamic", use_container_width=True)
    st.session_state.mis_trades = edited_df

    if st.button("🔄 Actualizar Estatus de Salida"):
        alertas = []
        for index, row in st.session_state.mis_trades.iterrows():
            m = analizar_ticker(row['Ticker'])
            if m:
                ganancia = (m['Precio'] - row['Precio_Entrada']) / row['Precio_Entrada']
                estado = "MANTENER"
                color = "white"
                if ganancia <= -stop_loss: 
                    estado, color = "🚨 VENDER (STOP LOSS)", "red"
                elif ganancia >= take_profit: 
                    estado, color = "✅ VENDER (PROFIT)", "green"
                elif m['R2'] < 0.65: 
                    estado, color = "📉 VENDER (DEGRADACIÓN)", "orange"
                
                alertas.append({"Ticker": row['Ticker'], "PnL %": f"{ganancia:.2%}", "Estado": estado})
        
        if alertas:
            st.write("Instrucciones de hoy:")
            st.table(pd.DataFrame(alertas))
