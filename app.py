import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time
import os
from datetime import datetime
import pytz
import json

# Configurar página
st.set_page_config(page_title="Stock Volume Tracker & SEC Alerts", layout="wide")

# Títulos y descripción
st.title("📊 Stock Rotation & Volume Tracker with SEC Alerts")

# Opciones de pestañas
menu = ["Monitoreo de Tickers", "SEC Files", "Historial"]
selection = st.sidebar.radio("Seleccione una opción", menu)

# Hora actual NY
ny_tz = pytz.timezone("America/New_York")
now_ny = datetime.now(ny_tz)

# Función para obtener datos de los tickers en tiempo real
def get_ticker_data(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            df = stock.history(period="1d", interval="1m")

            if df.empty:
                continue

            last_price = df["Close"].iloc[-1]
            open_price = df["Open"].iloc[0]
            volume = df["Volume"].sum()
            change = ((last_price - open_price) / open_price) * 100

            shares_float = info.get("floatShares", None)
            if shares_float:
                rotation = volume / shares_float
            else:
                rotation = None

            data.append({
                "Ticker": ticker,
                "Precio actual": round(last_price, 3),
                "Apertura": round(open_price, 3),
                "% Cambio": round(change, 2),
                "Volumen": f"{volume:,}",
                "Float": f"{shares_float:,}" if shares_float else "N/A",
                "Rotación del Float": round(rotation, 2) if rotation else "N/A"
            })
        except Exception as e:
            st.error(f"Error con {ticker}: {e}")
    return data

# Función para obtener archivos recientes de la SEC
def get_sec_files():
    url = "https://www.sec.gov/files/derivatives/otc-report.json"  # Aquí puedes agregar un endpoint de SEC
    try:
        response = requests.get(url)
        data = response.json()

        # Aquí, agregamos la lógica para extraer los archivos y sus detalles
        recent_files = data.get('files', [])  # Esto depende de cómo sea la estructura de los archivos

        # Guardamos los archivos ya descargados en el historial
        return recent_files
    except Exception as e:
        st.error(f"Error al obtener archivos de la SEC: {e}")
        return []

# Reproducir un sonido cuando un archivo es encontrado
def play_alert():
    alert_sound = os.path.join("assets", "alert_sound.mp3")
    st.audio(alert_sound)

# Mostrar los tickers y sus datos
if selection == "Monitoreo de Tickers":
    tickers_input = st.text_input("Escribe los tickers separados por comas", "AAPL, TSLA, MSFT")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]

    # Obtener los datos del ticker
    data = get_ticker_data(ticker_list)
    
    if data:
        df_display = pd.DataFrame(data)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.warning("No se encontraron datos.")

# Mostrar archivos de la SEC y alertas en tiempo real
elif selection == "SEC Files":
    st.markdown("### Archivos recientes de la SEC")

    # Obtenemos los archivos de la SEC cada segundo
    recent_files = []
    prev_files = set()

    while True:
        new_files = get_sec_files()
        for file in new_files:
            file_name = file.get("file_name", "")
            if file_name not in prev_files:
                # Si es un nuevo archivo, agregamos y activamos la alerta
                prev_files.add(file_name)
                recent_files.append(file)
                play_alert()  # Reproducir el sonido de alerta
                st.write(f"Nuevo archivo encontrado: {file_name}")
        
        # Mostrar los archivos recientes en tiempo real
        for file in recent_files:
            st.write(file)

        time.sleep(1)  # Esperar 1 segundo antes de revisar nuevamente

# Historial de archivos SEC
elif selection == "Historial":
    st.markdown("### Historial de Archivos SEC y Tickers")
    # Aquí puedes agregar la lógica para mostrar los archivos y tickers previos
    # Usar st.session_state para almacenar los históricos
    if "history" not in st.session_state:
        st.session_state.history = []
    
    st.session_state.history.append({
        "Tickers": ticker_list,
        "Fecha": str(now_ny)
    })
    
    for entry in st.session_state.history[-10:]:  # Mostrar solo los últimos 10
        st.write(entry)
