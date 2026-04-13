import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def obtener_datos_api():
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/",
        "Accept": "*/*"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # La API devuelve HTML, usamos pandas para convertirlo a tabla directamente
        if response.status_code == 200:
            # pd.read_html encuentra la tabla en el texto HTML que devuelve la API
            tablas = pd.read_html(response.text)
            return tablas[0], None
        else:
            return None, f"Error HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

if st.button('Obtener Tarifas Actualizadas'):
    with st.spinner('Consultando API...'):
        df, error = obtener_datos_api()
        
        if error:
            st.error(f"Error: {error}")
        else:
            st.success("¡Datos cargados correctamente desde la API!")
            st.dataframe(df, use_container_width=True)
            
            # Botón descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", csv, "tarifas_luz.csv", "text/csv")
