import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime, timezone
import warnings

warnings.filterwarnings('ignore')

# ==========================================================================
# 1. CONFIGURACIÓN E INTERFAZ CORPORATIVA UNIFICADA
# ==========================================================================
st.set_page_config(page_title="The One Ring: Momentum Bot v2.0", layout="wide", page_icon="🚀")

st.title("🚀 Momentum Strategy Bot v2.0 — Motor de Inercia Logarítmica")
st.caption("Ecosistema Cuantitativo 'The One Ring' | Optimizado para Asignación de Fracciones de Alta Velocidad")
st.markdown("---")

# BARRA LATERAL DE PARAMETRIZACIÓN
st.sidebar.header("⚙️ Parámetros de Control Táctico")
capital_total = st.sidebar.number_input("Capital Disponible para Despliegue (USD)", value=50000.0, step=1000.0)
st.sidebar.markdown("---")
stop_loss_pct = st.sidebar.slider("Stop Loss Máximo Permitido (%)", 1, 10, 4) / 100
take_profit_pct = st.sidebar.slider("Take Profit Objetivo (%)", 1, 20, 8) / 100

# MEJORA DE CAPTURA: Umbral por defecto flexibilizado a 0.65 para atrapar momentum volátil (AMD, ARM, Proxies)
umbral_r2_compra = st.sidebar.slider("Umbral R2 Mínimo de Calidad Lineal", 0.4, 0.9, 0.65)

# UNIVERSO INTEGRADO Y EXPANDIDO DE ALTA INERCIA (115 TICKERS INSTITUCIONALES)
UNIVERSO_COMPLETO = [
    "NVDA", "TSM", "AVGO", "ARM", "ASML", "MU", "AMD", "SMCI", "LRCX", "AMAT", "KLAC", "MRVL", "QCOM", "TER", "ADI", "NXPI", "TXN", "WDC",
    "MSFT", "GOOGL", "META", "AMZN", "PLTR", "CRM", "ADBE", "SNOW", "CRWD", "PANW", "ZS", "DDOG", "NOW", "TEAM", "WDAY", "SHOP", "NET", "MDB", "TTD", "ROKU",
    "GEV", "VST", "CEG", "CCJ", "SMR", "BWXT", "NEE", "XOM", "CVX", "TPL", "NFE", "OKE", "ET", "FANG", "LEU", "OKLO", "NXE", "UUUU",
    "MELI", "NU", "SQ", "PYPL", "HOOD", "COIN", "MSTR", "SE", "DLO", "UBER", "BABA", "PDD", "CPNG", "MARA", "RIOT", "SOFI",
    "LLY", "NVO", "VKTX", "HIMS", "VRTX", "REGN", "OSCR", "GILD", "AMGN", "ISRG", "PFE", "CRSP", "MRNA",
    "AVAV", "RKLB", "LMT", "RTX", "CAT", "DE", "GE", "ETN", "URI", "GD", "NOC", "TDG", "HON", "WM", "KTOS",
    "NFLX", "AAPL", "COST", "WMT", "JPM", "V", "MA", "TSLA", "MCO", "SPGI", "ADP", "BAC", "MS", "GS", "BLK", "CELH", "ON"
]
TICKERS = list(set(UNIVERSO_COMPLETO))

# ==========================================================================
# 2. MOTOR DE CÓMPUTO: REGRESIÓN DE INERCIA LOGARÍTMICA
# ==========================================================================
def analizar_ticker(ticker):
    try:
        raw = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if raw.empty: return None
        
        if isinstance(raw.columns, pd.MultiIndex):
            data = raw['Close'][ticker]
        else:
            data = raw['Close']
            
        data = data.squeeze().dropna()
        if len(data) < 90: return None
        
        # Regresión Logarítmica sobre la ventana móvil de los últimos 90 días
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

# ==========================================================================
# 3. INTERFAZ GRÁFICA MULTIPÁGINA COMPATIBLE
# ==========================================================================
tab1, tab2 = st.tabs(["🔍 Escáner de Inercia Dinámica", "📊 Monitor de Portafolio Real"])

with tab1:
    if st.button("🚀 Iniciar Escaneo de Cobertura Global"):
        with st.spinner(f"Triturando curvas logarítmicas en {len(TICKERS)} activos activos..."):
            resultados = []
            for t in TICKERS:
                res = analizar_ticker(t)
                if res: resultados.append(res)
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # --- SECCIÓN 1: SUGERENCIAS DE COMPRA AUTOMATIZADAS ---
                st.subheader("✅ Señales de Entrada de Alta Inercia (Filtro R² Activo)")
                df_gan = df[(df['R2'] >= umbral_r2_compra) & (df['Sobre_MA20'] == True)]
                
                if not df_gan.empty:
                    # Selección de las 5 mejores locomotoras del mercado por velocidad
                    df_gan = df_gan.sort_values(by="Momentum_Anual", ascending=False).head(5)
                    # Gestión de capital proporcional normalizado a la calidad lineal
                    df_gan['Inversión_USD'] = (df_gan['R2'] / df_gan['R2'].sum()) * capital_total
                    df_gan['Fracciones a Comprar'] = round(df_gan['Inversión_USD'] / df_gan['Precio'], 4)
                    
                    st.success("🎯 **ASIGNACIÓN PRESUPUESTAL COMPLETADA:** Posturas optimizadas proporcionalmente según el coeficiente de calidad R².")
                    st.dataframe(df_gan[['Ticker', 'Momentum_Anual', 'R2', 'Inversión_USD', 'Fracciones a Comprar']]
                                 .style.format({"Momentum_Anual": "{:.2%}", "R2": "{:.3f}", "Inversión_USD": "${:,.2f}"}),
                                 use_container_width=True, hide_index=True)
                else:
                    st.info("El mercado cotiza en rango lateral o distribución. No hay activos que cumplan el filtro de inercia limpia actual.")
                
                # --- SECCIÓN 2: WATCHLIST GLOBAL DE VELOCIDAD ---
                st.markdown("---")
                st.subheader("🔭 Top 10 Líderes de Momentum General (Vigilancia)")
                st.table(df.sort_values(by="Momentum_Anual", ascending=False).head(10)[['Ticker', 'Momentum_Anual', 'R2', 'Sobre_MA20']]
                         .style.format({"Momentum_Anual": "{:.2%}", "R2": "{:.3f}"}))
            else:
                st.error("No se pudo establecer la conexión con las series históricas financieras.")

with tab2:
    st.header("🛡️ Consola de Gestión de Riesgos y Salidas")
    
    if 'mis_trades' not in st.session_state:
        st.session_state.mis_trades = pd.DataFrame(columns=["Ticker", "Cantidad_Acciones", "Precio_Entrada"])
        st.session_state.mis_trades = st.session_state.mis_trades.astype({"Cantidad_Acciones": float, "Precio_Entrada": float})

    st.info("💡 **Guía de Control:** Registra tus fracciones vivas. Al presionar 'Actualizar Estatus', el sistema auditará las reglas de salida paramétricas de forma automática.")
    
    edited_df = st.data_editor(st.session_state.mis_trades, num_rows="dynamic", use_container_width=True)
    st.session_state.mis_trades = edited_df

    col_a, col_b = st.columns([1, 4])
    with col_a:
        check_salida = st.button("🔄 Actualizar Estatus", use_container_width=True)
    with col_b:
        if st.button("🗑️ Resetear Consola", use_container_width=True):
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
                
                # PROTOCOLO DE SALIDA TOTALMENTE REFACTORIZADO (INYECCIÓN DE REGLA ACELERADA)
                if gan_pct >= take_profit_pct:
                    estado = "⚡ LIQUIDACIÓN INMEDIATA (TAKE PROFIT ACELERADO)"
                elif gan_pct <= -stop_loss_pct: 
                    estado = "🚨 LIQUIDACIÓN OBLIGATORIA (STOP LOSS COMPROMETIDO)"
                elif m['R2'] < 0.55: 
                    estado = "📉 VENTA TÉCNICA (DEGRADACIÓN ESTRUCTURAL DEL R²)"
                else:
                    estado = "🟢 MANTENER POSICIÓN EN TENDENCIA"
                
                alertas.append({
                    "Ticker": ticker,
                    "Fracciones": cant,
                    "Precio Entrada": f"${p_ent:,.2f}",
                    "Precio Actual": f"${p_act:,.2f}",
                    "Variación %": f"{gan_pct:.2%}",
                    "PnL Absoluto (USD)": f"${gan_usd:,.2f}",
                    "Dictamen de Isengard": estado
                })
        
        if alertas:
            st.markdown("---")
            st.subheader("📋 Ordenanza Ejecutiva de Operaciones del Fondo")
            
            def style_alerts(val):
                if "TAKE PROFIT" in val: return "background-color: #f0fff4; color: #1b7f3a; font-weight: bold;"
                if "STOP LOSS" in val: return "background-color: #fff5f5; color: #b00020; font-weight: bold;"
                if "DEGRADACIÓN" in val: return "background-color: #fffaf0; color: #dd6b20;"
                return "color: #1a202c;"

            df_alertas = pd.DataFrame(alertas)
            st.dataframe(df_alertas.style.map(style_alerts, subset=["Dictamen de Isengard"]), use_container_width=True, hide_index=True)
        else:
            st.info("No se han detectado variaciones críticas en el portafolio registrado.")
