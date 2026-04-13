import streamlit as st
import pandas as pd
import requests
import io

# Configuración de la interfaz
st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def obtener_datos_api():
    # URL de la API identificada en el cURL
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/",
        "Accept": "*/*"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            # Convertimos el texto HTML en un stream para que pandas lo lea correctamente
            html_io = io.StringIO(response.text)
            # read_html devuelve una lista de DataFrames encontrados en el HTML
            tablas = pd.read_html(html_io)
            
            if tablas:
                return tablas[0], None
            else:
                return None, "No se encontraron tablas en la respuesta."
        else:
            return None, f"Error HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

# Interfaz principal
if st.button('Obtener Tarifas Actualizadas'):
    with st.spinner('Consultando la API de tarifas...'):
        df, error = obtener_datos_api()
        
        if error:
            st.error(f"Error: {error}")
        else:
            st.success("¡Datos cargados correctamente!")
            st.dataframe(df, use_container_width=True)
            
            # Preparar descarga de CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos como CSV",
                data=csv,
                file_name='tarifas_luz.csv',
                mime='text/csv'
            )
