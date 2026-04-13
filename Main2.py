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
    response = requests.get(url, headers=headers, timeout=20)
    html_io = io.StringIO(response.text)
    return pd.read_html(html_io)[0]

if st.button('Procesar y Limpiar Tarifas'):
    df = obtener_datos()
    
    # Lista para almacenar las filas limpias
    datos_limpios = []
    compania_actual = None
    
    # Iteramos sobre la tabla original para reconstruirla
    for _, fila in df.iterrows():
        # Asumimos que si la columna 'Tarifa' (índice 2) es 'None', 
        # podría ser una fila de compañía o una fila vacía
        valor_tarifa = str(fila.iloc[2])
        
        # Si la fila tiene un nombre de compañía (podemos detectar esto si tiene sentido)
        # o simplemente ignoramos las filas que son puramente 'None'
        if valor_tarifa != 'None' and 'Potencia' in str(fila.iloc[3]):
            datos_limpios.append({
                "Tarifa": valor_tarifa,
                "Detalles": fila.iloc[3] # Aquí están tus precios
            })
            
    df_limpio = pd.DataFrame(datos_limpios)
    
    st.subheader("Tabla Final Limpia")
    st.dataframe(df_limpio, use_container_width=True)
    
    csv = df_limpio.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar CSV Limpio", csv, "tarifas_limpias.csv", "text/csv")
