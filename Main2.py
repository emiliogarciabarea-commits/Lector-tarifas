import streamlit as st
import pandas as pd
import requests
import io

# Configuración de la interfaz
st.set_page_config(page_title="Tarifas Luz Limpias", layout="wide")
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
        if response.status_code == 200:
            html_io = io.StringIO(response.text)
            tablas = pd.read_html(html_io)
            if tablas:
                return tablas[0], None
            else:
                return None, "No se encontraron tablas."
        else:
            return None, f"Error HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

# Interfaz principal
if st.button('Obtener Tarifas Actualizadas'):
    with st.spinner('Consultando y limpiando datos...'):
        df_original, error = obtener_datos_api()
        
        if error:
            st.error(f"Error: {error}")
        else:
            # 1. Seleccionamos solo las columnas que te interesan
            # Nota: Ajustamos los nombres según suelen venir en la tabla de esa web
            columnas_interes = ['Tarifa', 'P1', 'P2', 'P3', 'E1', 'E2', 'E3', 'FV']
            
            # Filtramos solo las columnas que existan en el DF para evitar errores
            columnas_reales = [c for c in columnas_interes if c in df_original.columns]
            df_limpio = df_original[columnas_reales].copy()

            # 2. Limpieza de filas vacías
            # Convertimos a numérico lo que deba serlo para detectar nulos correctamente
            cols_precios = ['P1', 'P2', 'P3', 'E1', 'E2', 'E3']
            for col in cols_precios:
                if col in df_limpio.columns:
                    # Reemplazamos comas por puntos y pasamos a número
                    df_limpio[col] = pd.to_numeric(df_limpio[col].astype(str).str.replace(',', '.'), errors='coerce')

            # 3. ELIMINAR FILAS SIN DATOS: 
            # Si P1 y E1 son nulos (NaN), la fila no nos interesa
            df_limpio = df_limpio.dropna(subset=['P1', 'E1'], how='all')

            st.success("¡Tabla limpia generada!")
            
            # Mostramos la tabla resultante
            st.dataframe(df_limpio, use_container_width=True)
            
            # Botón para descargar la versión limpia
            csv = df_limpio.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar Tabla Limpia (CSV)",
                data=csv,
                file_name='tarifas_luz_limpias.csv',
                mime='text/csv'
            )
