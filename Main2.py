import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formateado")

def extraer_precio(texto, patron):
    # Busca el patrón (ej: "P1: 0,12") y extrae el número
    match = re.search(f"{patron}:\s*([\d,]+)", texto)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

def obtener_datos():
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"}
    response = requests.get(url, headers=headers, timeout=20)
    html_io = io.StringIO(response.text)
    return pd.read_html(html_io)[0]

if st.button('Generar Tabla Formateada'):
    df = obtener_datos()
    datos_finales = []
    
    for _, fila in df.iterrows():
        tarifa = str(fila.iloc[2])
        detalles = str(fila.iloc[3])
        
        if tarifa != 'None' and 'Potencia' in detalles:
            # Extraer valores básicos
            p1 = extraer_precio(detalles, "P1")
            p2 = extraer_precio(detalles, "P2") or p1 # Si no hay P2, es P1
            p3 = extraer_precio(detalles, "P3") or p2
            
            e1 = extraer_precio(detalles, "E1")
            e2 = extraer_precio(detalles, "E2") or e1
            e3 = extraer_precio(detalles, "E3") or e2
            fv = extraer_precio(detalles, "Fv") or 0.0
            
            datos_finales.append({
                "Tarifa": tarifa,
                "P1": p1, "P2": p2, "P3": p3,
                "E1": e1, "E2": e2, "E3": e3,
                "FV": fv
            })
            
    df_final = pd.DataFrame(datos_finales)
    st.dataframe(df_final, use_container_width=True)
