import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def obtener_datos():
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            # Usamos StringIO para evitar errores de archivo
            html_io = io.StringIO(response.text)
            tablas = pd.read_html(html_io)
            if tablas:
                return tablas[0], None
            return None, "No se encontraron tablas en la respuesta."
        return None, f"Error HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

if st.button('Obtener Tarifas'):
    with st.spinner('Procesando...'):
        df, error = obtener_datos()
        
        if error:
            st.error(error)
        else:
            # 1. Limpiar nombres de columnas (quitar espacios, etc)
            df.columns = df.columns.str.strip()
            
            # 2. Mostrar todas las columnas detectadas para depurar
            st.write("Columnas detectadas:", df.columns.tolist())
            
            # 3. Filtrado seguro: buscamos columnas que contengan 'P1' o 'E1'
            # Esto evita el KeyError si el nombre es ligeramente distinto
            cols_p = [c for c in df.columns if 'P1' in c]
            cols_e = [c for c in df.columns if 'E1' in c]
            
            if cols_p and cols_e:
                # Solo limpiar si las columnas existen
                df_limpio = df.dropna(subset=[cols_p[0], cols_e[0]], how='all')
                st.dataframe(df_limpio)
            else:
                st.warning("No se encontraron columnas P1/E1 estándar. Mostrando tabla original:")
                st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", csv, "tarifas.csv", "text/csv")
