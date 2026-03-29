import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime
import warnings

# Configuración de Silencio para advertencias
warnings.filterwarnings('ignore')

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ
# ==========================================
st.set_page_config(page_title="Momentum Strategy Bot v1.7", layout="wide")

st.title("🚀 Momentum Strategy Bot v1.7")
st.markdown("---")

# BARRA LATERAL - PARÁMETROS
st.sidebar.header("⚙️ Parámetros de Estrategia")
capital_total = st.sidebar.number_input("Capital Disponible (USD)", value=50000)
stop_loss_pct = st.sidebar.slider("Stop Loss (%)", 1, 10, 4) / 100
take_profit_pct = st.sidebar.slider("Take Profit (%)", 1, 20, 8) / 100
umbral_r2_compra = st.sidebar.slider("Umbral R2 (Calidad de Entrada)", 0.5, 0.9, 0.8)
umbral_r2_salida = 0.65 # Salida por degradación de tendencia

# UNIVERSO DE ACTIVOS (Expandido)
TICKERS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "ARM", "SMCI", "AMD", "INTC", "TSM", "ASML", "MU", "WDC", "MRVL",
    "PLTR", "ORCL", "ADBE", "CRM", "SNOW", "PANW", "CRWD", "NET", "NOW",
    "GEV", "VST", "CEG", "CCJ", "LEU", "OKLO", "SMR", "NXE", "BWXT", "XOM", "CVX", "SLB", "HAL",
    "COIN", "MSTR", "MARA", "RIOT", "HOOD", "SOFI", "NU", "PYPL", "V", "MA",
    "LLY", "NVO", "VKTX", "UNH", "JNJ", "ABBV", "AMGN",
    "AVAV", "KTOS", "RKLB", "LMT", "RTX", "NOC", "LHX",
    "WMT", "TGT", "COST", "HD", "LOW", "NKE", "SBUX", "EL",
    "JPM", "BAC", "GS", "MS", "BRK-B", "CAT", "DE", "BA", "DIS"
]

# ==========================================
# 2. MOTOR DE ANÁLISIS ROBUSTO (v1.7)
# ==========================================
def analizar_ticker(ticker):
    try:
        # Descarga de 1 año para asegurar datos suficientes
        raw = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if raw.empty: return None
        
        # Aplanamiento de datos Multi-Index (Protección contra errores de Yahoo)
        if isinstance(raw.columns, pd.MultiIndex):
            data = raw['Close'][ticker]
        else:
            data = raw['Close']
            
        data = data.squeeze().dropna()
        if len(data) < 90: return None
        
        # Regresión Logarítmica (Inercia)
        serie = data.tail(90)
        log_prices = np.log(serie)
        x = np.arange(len(log_prices))
        y = log_prices.values # Forzamos valores numéricos para evitar UFuncNoLoopError
        
        slope, _, r_val, _, _ = linregress(x, y)
        
        return {
            "Ticker": ticker,
            "Precio": round(float(data.iloc[-1]), 2),
            "Momentum_Anual": round((np.exp(slope) ** 252) - 1, 4),
            "R2": round(float(r_val**2), 4),
            "Sobre_MA20": bool(data.iloc[-1] > data.rolling(20).mean().iloc[-1])
        }
    except:
        return None

# ==========================================
# 3. INTERFAZ DE USUARIO (TABS)
# ==========================================
tab1, tab2 = st.tabs(["🔍 Escáner de Mercado", "📊 Mi Portafolio"])

# --- TAB 1: ESCÁNER ---
with tab1:
    col1, col2 = st.columns([1, 4])
    with col1:
        ejecutar = st.button("🚀 Ejecutar Escaneo")
    
    if ejecutar:
        with st.spinner(f"Analizando {len(TICKERS)} activos..."):
            resultados = []
            barra_progreso = st.progress(0)
            for i, t in enumerate(TICKERS):
                res = analizar_ticker(t)
                if res: resultados.append(res)
                barra_progreso.progress((i + 1) / len(TICKERS))
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # SECCIÓN A: SEÑALES DE COMPRA
                st.subheader("✅ Señales de Compra (Alta Convicción)")
                df_ganadores = df[(df['R2'] >= umbral_r2_compra) & (df['Sobre_MA20'] == True)]
                
                if not df_ganadores.empty:
                    df_ganadores = df_ganadores.sort_values(by="Momentum_Anual", ascending=False).head(5)
                    # Cálculo de pesos dinámicos
                    df_ganadores['Inversión_USD'] = (df_ganadores['R2'] / df_ganadores['R2'].sum()) * capital_total
                    df_ganadores['Acciones'] = (df_ganadores['Inversión_USD'] / df_ganadores['Precio']).apply(np.floor)
                    st.dataframe(df_ganadores[['Ticker', 'Momentum_Anual', 'R2', 'Inversión_USD', 'Acciones']], use_container_width=True)
                else:
                    st.info("Sin señales de alta calidad hoy. El mercado está ruidoso.")

                # SECCIÓN B: WATCHLIST (EL TOP 10 DE MOMENTUM)
                st.subheader("🔭 Candidatos en Observación (Top Inercia)")
                df_watch = df.sort_values(by="Momentum_Anual", ascending=False).head(10)
                st.table(df_watch[['Ticker', 'Momentum_Anual', 'R2', 'Sobre_MA20']])
            else:
                st.error("No se pudieron obtener datos del mercado.")

# --- TAB 2: PORTAFOLIO ---
with tab2:
    st.header("Seguimiento de Posiciones")
    
    # Inicialización de la Bitácora
    if 'mis_trades' not in st.session_state:
        st.session_state.mis_trades = pd.DataFrame(
            columns=["Ticker", "Precio_Entrada", "Fecha"]
        ).astype({"Precio_Entrada": float})

    st.write("Escribe tus compras. Selecciona una fila y presiona 'Suprimir' para borrar.")
    
    # Editor de datos interactivo
    edited_df = st.data_editor(st.session_state.mis_trades, num_rows="dynamic", use_container_width=True)
    st.session_state.mis_trades = edited_df

    col_a, col_b = st.columns([1, 4])
    with col_a:
        check_salida = st.button("🔄 Actualizar Estatus")
    with col_b:
        if st.button("🗑️ Limpiar Todo"):
            st.session_state.mis_trades = pd.DataFrame(columns=["Ticker", "Precio_Entrada", "Fecha"])
            st.rerun()

    if check_salida:
        alertas = []
        for index, row in st.session_state.mis_trades.iterrows():
            try:
                # Sanitización de datos de entrada
                ticker = str(row['Ticker']).strip().upper()
                p_entrada = float(row['Precio_Entrada'])
                if not ticker or p_entrada <= 0: continue
            except:
                continue

            m = analizar_ticker(ticker)
            if m:
                p_actual = float(m['Precio'])
                ganancia = (p_actual - p_entrada) / p_entrada
                
                # Lógica de salida
                estado = "🟢 MANTENER"
                if ganancia <= -stop_loss_pct: estado = "🚨 VENDER (STOP LOSS)"
                elif ganancia >= take_profit_pct: estado = "✅ VENDER (PROFIT)"
                elif m['R2'] < umbral_r2_salida: estado = "📉 VENDER (DEGRADACIÓN)"
                
                alertas.append({
                    "Ticker": ticker, 
                    "Precio Ent.": p_entrada,
                    "Precio Act.": p_actual,
                    "PnL %": f"{ganancia:.2%}", 
                    "Estado": estado
                })
        
        if alertas:
            st.subheader("📋 Instrucciones de Operación")
            st.dataframe(pd.DataFrame(alertas), use_container_width=True)
        else:
            st.info("Registra posiciones válidas (Ticker y Precio) para ver el análisis.")
