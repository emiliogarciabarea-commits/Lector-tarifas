import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas - Ajuste Preciso FV")

def extraer_fv(texto):
    # BUSCAMOS EXACTAMENTE: "Fv: 0,0500 €/kWh"
    # 1. Busca "Fv:" ignorando mayúsculas
    # 2. Captura los números decimales
    # 3. Exige que terminen en "€/kWh" (o espacio y símbolo)
    regex = r"Fv:\s*([\d]+[\.,][\d]+)\s*€/kWh"
    
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return 0.0

def extraer_valor(texto, etiqueta):
    # Para P1, E1, etc., mantenemos la lógica anterior
    regex = f"{etiqueta}.*?[:\s]+([0-9]+[.,][0-9]+)"
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return 0.0

if st.button('Generar Tabla Precisa'):
    try:
        url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=20)
        df = pd.read_html(io.StringIO(response.text))[0]
        
        datos = []
        for _, fila in df.iterrows():
            texto_fila = " ".join([str(x) for x in fila.values])
            
            if "Potencia" in texto_fila:
                # Cortamos el texto en FBS para que no exista para el buscador
                texto_limpio = re.split(r'FBS', texto_fila, flags=re.IGNORECASE)[0]
                
                # Extraemos valores
                fv = extraer_fv(texto_limpio) # Usamos nuestra nueva función precisa
                
                datos.append({
                    "Tarifa": str(fila.iloc[2]),
                    "P1": extraer_valor(texto_limpio, "P1"),
                    "E1": extraer_valor(texto_limpio, "E1"),
                    "FV": fv
                })
        
        st.dataframe(pd.DataFrame(datos), use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")
