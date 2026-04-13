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
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            # Usamos StringIO para procesar el texto HTML de la API
            html_io = io.StringIO(response.text)
            tablas = pd.read_html(html_io)
            if tablas:
                return tablas[0], None
            return None, "No se encontraron tablas."
        return None, f"Error HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

# Ejecución al pulsar el botón
if st.button('Obtener Tarifas Actualizadas'):
    with st.spinner('Consultando y filtrando datos...'):
        df, error = obtener_datos_api()
        
        if error:
            st.error(f"Error: {error}")
        else:
            # 1. Limpieza de nombres de columnas (quitar espacios invisibles)
            df.columns = df.columns.str.strip()

            # 2. Selección de columnas de interés
            # Definimos las que quieres ver
            columnas_target = ['Tarifa', 'P1', 'P2', 'P3', 'E1', 'E2', 'E3', 'FV']
            # Solo seleccionamos las que realmente existan en el DF
            existentes = [c for c in columnas_target if c in df.columns]
            df_final = df[existentes].copy()

            # 3. FILTRO ANTI-NONE: 
            # Convertimos a número para identificar qué es "None" o texto vacío
            for col in df_final.columns:
                if col != 'Tarifa':
                    df_final[col] = pd.to_numeric(df_final[col].astype(str).str.replace(',', '.'), errors='coerce')

            # Eliminamos cualquier fila donde la columna 'Tarifa' sea nula o 
            # donde P1 y E1 no tengan datos (así quitamos las filas vacías)
            # Buscamos las columnas de potencia y energía disponibles
            c_p1 = [c for c in df_final.columns if 'P1' in c]
            c_e1 = [c for c in df_final.columns if 'E1' in c]
            
            subset_filtro = []
            if c_p1: subset_filtro.append(c_p1[0])
            if c_e1: subset_filtro.append(c_e1[0])

            if subset_filtro:
                # dropna con 'all' elimina la fila si todos los campos del subset son None
                df_final = df_final.dropna(subset=subset_filtro, how='all')
            
            # También eliminamos si el nombre de la tarifa es "None" o está vacío
            df_final = df_final[df_final['Tarifa'].fillna('').str.strip().lower() != 'none']
            df_final = df_final.dropna(subset=['Tarifa'])

            st.success(f"Se han encontrado {len(df_final)} tarifas válidas.")
            
            # Mostrar tabla
            st.dataframe(df_final, use_container_width=True)
            
            # Botón de descarga
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Tabla Limpia (CSV)", csv, "tarifas_luz.csv", "text/csv")
