import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# 1. CONFIGURACIÓN E INTERFAZ
# ==========================================
st.set_page_config(page_title="Momentum Bot v1.8 (Fractional)", layout="wide")

st.title("🚀 Momentum Strategy Bot v1.8")
st.caption("Optimizado para Trading de Fracciones (GBM US) | Enfoque: Alta Inercia 3-10 Días")
st.markdown("---")

# BARRA LATERAL
st.sidebar.header("⚙️ Configuración")
capital_total = st.sidebar.number_input("Capital Disponible (USD)", value=50000.0, step=1000.0)
stop_loss_pct = st.sidebar.slider("Stop Loss (%)", 1, 10, 4) / 100
take_profit_pct = st.sidebar.slider("Take Profit (%)", 1, 20, 8) / 100
umbral_r2_compra = st.sidebar.slider("Umbral R2 (Calidad)", 0.5, 0.9, 0.8)

# UNIVERSO MOMENTUM (Actualizado con tu lista social y estratégica)
TICKERS = [
    # --- IA & SEMICONDUCTORES (Alta Volatilidad) ---
    "NVDA", "AMD", "AVGO", "ARM", "SMCI", "TSM", "ASML", "MU", "WDC", "MRVL", "AMAT", "KLAC", "LRCX",
    # --- SOFTWARE & CLOUD GROWTH ---
    "PLTR", "ORCL", "ADBE", "CRM", "SNOW", "PANW", "CRWD", "NET", "NOW", "DDOG", "MDB", "SHOP", "TTD", "ROKU",
    # --- ENERGÍA NUCLEAR & FRONTIER ENERGY ---
    "GEV", "VST", "CEG", "CCJ", "LEU", "OKLO", "SMR", "NXE", "BWXT", "UUUU",
    # --- CRYPTO PROXIES & FINTECH AGRESIVA ---
    "COIN", "MSTR", "MARA", "RIOT", "HOOD", "SOFI", "NU", "PYPL", "SQ", "MELI",
    # --- SALUD & BIOTECH (Growth) ---
    "LLY", "NVO", "VKTX", "HIMS", "CRSP", "MRNA",
    # --- DEFENSA & ESPACIO ---
    "RKLB", "AVAV", "KTOS", "LMT", "RTX", "NOC",
    # --- CONSUMO & GROWTH CHINA ---
    "AMZN", "TSLA", "CELH", "ON", "NFLX", "BABA", "PDD", "COST", "WMT"
]

# ==========================================
# 2. MOTOR DE ANÁLISIS
# ==========================================
def analizar_ticker(ticker):
    try:
        # Descarga de 1 año para tener historial de MA20 y Regresión de 90d
        raw = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if raw.empty: return None
        
        # Aplanado de columnas para evitar errores MultiIndex
        if isinstance(raw.columns, pd.MultiIndex):
            data = raw['Close'][ticker]
        else:
            data = raw['Close']
            
        data = data.squeeze().dropna()
        if len(data) < 90: return None
        
        # Regresión Logarítmica (Inercia de los últimos 90 días)
        serie = data.tail(90)
        log_prices = np.log(serie)
        slope, _, r_val, _, _ = linregress(np.arange(len(log_prices)), log_prices.values)
        
        return {
            "Ticker": ticker,
            "Precio": round(float(data.iloc[-1]), 2),
            "Momentum_Anual": round((np.exp(slope) ** 252) - 1, 4),
            "R2": round(float(r_val**2), 4),
            "Sobre_MA20": bool(data.iloc[-1] > data.rolling(20).mean().iloc[-1])
        }
    except: return None

# ==========================================
# 3. TABS DE NAVEGACIÓN
# ==========================================
tab1, tab2 = st.tabs(["🔍 Escáner de Momentum", "📊 Mi Portafolio Real"])

with tab1:
    if st.button("🚀 Ejecutar Escaneo Diario"):
        with st.spinner(f"Analizando inercia en {len(TICKERS)} activos..."):
            resultados = []
            for t in TICKERS:
                res = analizar_ticker(t)
                if res: resultados.append(res)
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # SECCIÓN 1: COMPRAS SUGERIDAS
                st.subheader("✅ Sugerencias de Compra (Inercia Limpia)")
                df_gan = df[(df['R2'] >= umbral_r2_compra) & (df['Sobre_MA20'] == True)]
                
                if not df_gan.empty:
                    # Top 5 por Momentum Anualizado
                    df_gan = df_gan.sort_values(by="Momentum_Anual", ascending=False).head(5)
                    # Ponderación por Calidad (R2)
                    df_gan['Inversión_USD'] = (df_gan['R2'] / df_gan['R2'].sum()) * capital_total
                    # Cálculo de Fracciones
                    df_gan['Acciones_a_Comprar'] = round(df_gan['Inversión_USD'] / df_gan['Precio'], 4)
                    
                    st.dataframe(df_gan[['Ticker', 'Momentum_Anual', 'R2', 'Inversión_USD', 'Acciones_a_Comprar']], use_container_width=True)
                else:
                    st.info("Sin señales de alta convicción (R2 alto + Sobre MA20) en este momento.")
                
                # SECCIÓN 2: WATCHLIST (MÁXIMO MOMENTUM)
                st.subheader("🔭 Top 10 Momentum (Vigilancia)")
                st.table(df.sort_values(by="Momentum_Anual", ascending=False).head(10)[['Ticker', 'Momentum_Anual', 'R2', 'Sobre_MA20']])
            else:
                st.error("No se pudieron obtener datos del mercado.")

with tab2:
    st.header("Gestión de Posiciones")
    
    if 'mis_trades' not in st.session_state:
        st.session_state.mis_trades = pd.DataFrame(
            columns=["Ticker", "Cantidad_Acciones", "Precio_Entrada"]
        ).astype({"Cantidad_Acciones": float, "Precio_Entrada": float})

    st.info("Tip: Para borrar una posición, selecciónala y presiona 'Delete' en tu teclado.")
    
    # Editor de datos interactivo para fracciones
    edited_df = st.data_editor(st.session_state.mis_trades, num_rows="dynamic", use_container_width=True)
    st.session_state.mis_trades = edited_df

    col_a, col_b = st.columns([1, 4])
    with col_a:
        check_salida = st.button("🔄 Actualizar Estatus")
    with col_b:
        if st.button("🗑️ Resetear Portafolio"):
            st.session_state.mis_trades = pd.DataFrame(columns=["Ticker", "Cantidad_Acciones", "Precio_Entrada"])
            st.rerun()

    if check_salida:
        alertas = []
        for index, row in st.session_state.mis_trades.iterrows():
            try:
                ticker = str(row['Ticker']).strip().upper()
                cant = float(row['Cantidad_Acciones'])
                p_ent = float(row['Precio_Entrada'])
                if not ticker or cant <= 0: continue
            except: continue

            m = analizar_ticker(ticker)
            if m:
                p_act = float(m['Precio'])
                gan_pct = (p_act - p_ent) / p_ent
                gan_usd = (p_act - p_ent) * cant
                
                estado = "🟢 MANTENER"
                if gan_pct <= -stop_loss_pct: 
                    estado = "🚨 VENDER (STOP LOSS)"
                elif gan_pct >= take_profit_pct: 
                    estado = "✅ VENDER (TAKE PROFIT)"
                elif m['R2'] < 0.65: 
                    estado = "📉 VENDER (DEGRADACIÓN R2)"
                
                alertas.append({
                    "Ticker": ticker,
                    "Cant.": cant,
                    "PnL %": f"{gan_pct:.2%}",
                    "PnL USD": f"${gan_usd:,.2f}",
                    "Estado": estado
                })
        
        if alertas:
            st.subheader("📋 Instrucciones de Operación")
            st.dataframe(pd.DataFrame(alertas), use_container_width=True)
        else:
            st.info("Registra posiciones (Ticker, Cantidad y Precio) para ver el estatus de salida.")
