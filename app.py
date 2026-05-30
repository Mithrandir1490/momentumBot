import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ==========================================================================
# 1. CONFIGURACIÓN E INTERFAZ CORPORATIVA UNIFICADA
# ==========================================================================
st.set_page_config(page_title="The One Ring: Momentum Bot v2.0", layout="wide", page_icon="🚀")

st.title("🚀 Momentum Strategy Bot v2.0 — Motor de Inercia Logarítmica")
st.caption("Ecosistema Cuantitativo 'The One Ring' | Optimizado para Asignación de Fracciones de Alta Velocidad")
st.markdown("---")

# RESTRICCIÓN DE PISO MÍNIMO INSTITUCIONAL POR OPERACIÓN
MIN_USD_PER_ORDER = 10.0

# BARRA LATERAL DE PARAMETRIZACIÓN
st.sidebar.header("⚙️ Parámetros de Control Táctico")

# MEJORA ACCESIBLE: El presupuesto de despliegue queda abierto para los socios (Default: Santiago's allocation)
presupuesto_diario_bot3 = st.sidebar.number_input("Presupuesto de Despliegue Hoy (USD)", value=139.82, step=50.0)
st.sidebar.markdown("---")

stop_loss_pct = st.sidebar.slider("Stop Loss Máximo Permitido (%)", 1, 10, 4) / 100
take_profit_pct = st.sidebar.slider("Take Profit Objetivo (%)", 1, 20, 8) / 100

# Umbral por defecto flexibilizado a 0.65 para atrapar momentum volátil (AMD, ARM, Proxies)
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
        with st.spinner(f"Triturando curvas logarítmicas en {len(TICKERS)} activos..."):
            resultados = []
            for t in TICKERS:
                res = analizar_ticker(t)
                if res: resultados.append(res)
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # --- SECCIÓN 1: SUGERENCIAS DE COMPRA AUTOMATIZADAS ---
                st.subheader("✅ Señales de Entrada de Alta Inercia (Filtro R² Activo)")
                df_gan = df[(df['R2'] >= umbral_r2_compra) & (df['Sobre_MA20'] == True)]
                n_gan = len(df_gan)
                
                if n_gan > 0:
                    # Selección de las 5 mejores locomotoras del mercado por velocidad
                    df_gan = df_gan.sort_values(by="Momentum_Anual", ascending=False).head(5)
                    n_final_buys = len(df_gan)
                    
                    # 1. Asignación proporcional base según el Coeficiente R2
                    pesos_base = df_gan['R2'] / df_gan['R2'].sum()
                    df_gan['Inversión_USD'] = pesos_base * presupuesto_diario_bot3
                    
                    # 2. Algoritmo de Optimización con Restricción de Piso de $10 USD
                    if presupuesto_diario_bot3 >= (n_final_buys * MIN_USD_PER_ORDER):
                        monto_insuficiente = True
                        while monto_insuficiente:
                            bajo_piso = df_gan['Inversión_USD'] < MIN_USD_PER_ORDER
                            
                            if bajo_piso.any():
                                df_gan.loc[bajo_piso, 'Inversión_USD'] = MIN_USD_PER_ORDER
                                
                                fondos_fijos = df_gan[df_gan['Inversión_USD'] == MIN_USD_PER_ORDER]['Inversión_USD'].sum()
                                presupuesto_restante = presupuesto_diario_bot3 - fondos_fijos
                                
                                sobre_piso = df_gan['Inversión_USD'] > MIN_USD_PER_ORDER
                                if sobre_piso.any() and presupuesto_restante > 0:
                                    df_gan.loc[sobre_piso, 'Inversión_USD'] = (df_gan.loc[sobre_piso, 'R2'] / df_gan.loc[sobre_piso, 'R2'].sum()) * presupuesto_restante
                                else:
                                    monto_insuficiente = False
                            else:
                                monto_insuficiente = False
                    
                    # Recalcular columnas de salida con presupuestos normalizados
                    df_gan['Porcentaje del Presupuesto'] = (df_gan['Inversión_USD'] / presupuesto_diario_bot3) * 100
                    df_gan['Fracciones a Comprar'] = round(df_gan['Inversión_USD'] / df_gan['Precio'], 4)
                    
                    st.success(f"🎯 **ASIGNACIÓN PRESUPUESTAL COMPLETADA:** Distribución de los ${presupuesto_diario_bot3:.2f} USD ejecutada. Restricción de $10.00 USD mínimos por orden activa.")
                    st.dataframe(df_gan[['Ticker', 'Momentum_Anual', 'R2', 'Porcentaje del Presupuesto', 'Inversión_USD', 'Fracciones a Comprar']]
                                 .style.format({"Momentum_Anual": "{:.2%}", "R2": "{:.3f}", "Porcentaje del Presupuesto": "{:.1f}%", "Inversión_USD": "${:,.2f}"}),
                                 use_container_width=True, hide_index=True)
                else:
                    st.info(f"El mercado cotiza en rango lateral o distribución. No hay aceleración limpia. El presupuesto diario de **${presupuesto_diario_bot3:.2f} USD** se retiene líquido en tesorería.")
                
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

    st.info("💡 **Guía de Control:** Registra tus fracciones vivas. Al presionar 'Actualizar Estatus', el sistema auditará las reglas de salida de forma automática.")
    
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
                
                # PROTOCOLO DE SALIDA CON REGRESIÓN DE INERCIA Y TAKE PROFIT PARABÓLICO ACELERADO
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
