import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def obtener_datos():
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/147.0.0.0",
        "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
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
            # 1. Mostrar la tabla original intacta (como querías)
            st.subheader("Tabla Original")
            st.dataframe(df, use_container_width=True)
            
            # 2. Crear la tabla filtrada:
            # Seleccionamos la primera columna (iloc[:, 0]) y comprobamos que no sea "None"
            # Usamos astype(str) para asegurar que comparamos texto
            primera_col = df.iloc[:, 0].astype(str).str.lower()
            df_filtrada = df[primera_col != 'none']
            
            # 3. Mostrar la tabla nueva filtrada
            st.subheader("Tabla Filtrada (Sin filas con 'None' en la primera columna)")
            st.dataframe(df_filtrada, use_container_width=True)
            
            # Botón de descarga para la tabla filtrada
            csv = df_filtrada.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV Filtrado", csv, "tarifas_filtradas.csv", "text/csv")
