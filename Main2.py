import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formateado")

def extraer_precio(texto, patron):
    # 're.IGNORECASE' permite capturar "fv:", "Fv:", "FV:", etc.
    # El patrón busca el nombre del campo, seguido de opcionalmente otros caracteres y el número
    match = re.search(f"{patron}:\s*([\d,]+)", texto, re.IGNORECASE)
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
            # Extraer valores básicos usando la función mejorada
            p1 = extraer_precio(detalles, "P1")
            p2 = extraer_precio(detalles, "P2") or p1 
            p3 = extraer_precio(detalles, "P3") or p2
            
            e1 = extraer_precio(detalles, "E1")
            e2 = extraer_precio(detalles, "E2") or e1
            e3 = extraer_precio(detalles, "E3") or e2
            
            # Lógica para FV: si no existe, asignamos 0.0 explícitamente
            fv_raw = extraer_precio(detalles, "FV")
            fv = fv_raw if fv_raw is not None else 0.0
            
            datos_finales.append({
                "Tarifa": tarifa,
                "P1": p1, "P2": p2, "P3": p3,
                "E1": e1, "E2": e2, "E3": e3,
                "FV": fv
            })
            
    df_final = pd.DataFrame(datos_finales)
    
    # Mostrar la tabla final
    st.dataframe(df_final, use_container_width=True)
    
    # Opcional: botón de descarga
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar CSV Formateado", csv, "tarifas_formateadas.csv", "text/csv")
