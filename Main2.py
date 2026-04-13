import streamlit as st
import pandas as pd
import requests
import json
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def obtener_datos_limpios():
    # URL de la API
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        # Extraemos el contenido como texto
        texto = response.text
        
        # En lugar de usar read_html, usamos expresiones regulares para buscar los datos
        # Esto es mucho más robusto frente a errores de formato
        # Buscamos los bloques de tarifas (asumiendo un patrón común en la web)
        tarifas = re.findall(r'title="([^"]*)"', texto)
        
        datos = []
        for t in tarifas:
            if "Potencia" in t or "P1" in t:
                datos.append({"Info": t})
        
        if not datos:
            return None, "No se encontraron datos estructurados. El formato de la web cambió."
            
        return pd.DataFrame(datos), None
    except Exception as e:
        return None, str(e)

if st.button('Obtener Tarifas'):
    with st.spinner('Procesando...'):
        df, error = obtener_datos_limpios()
        
        if error:
            st.error(error)
        else:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", csv, "tarifas.csv", "text/csv")
