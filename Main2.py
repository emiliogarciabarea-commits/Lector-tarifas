import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Versión Corregida")

def obtener_datos():
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"}
    response = requests.get(url, headers=headers, timeout=20)
    return pd.read_html(io.StringIO(response.text))[0]

def limpiar_y_extraer(texto, patron):
    # regex mejorada: busca el patrón, ignora hasta los dos puntos y espacio, 
    # y exige decimales (punto o coma) para evitar capturar enteros (como '1')
    regex = f"{patron}.*?[:\s]+([\d]+[\.,][\d]+)"
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        valor = match.group(1).replace(',', '.')
        return float(valor)
    return None

if st.button('Generar Tabla Completa'):
    df = obtener_datos()
    datos_finales = []
    
    for _, fila in df.iterrows():
        tarifa = str(fila.iloc[2])
        detalles = str(fila.iloc[3])
        
        if tarifa != 'nan' and 'Potencia' in detalles:
            # Extracción normal para precios
            p1 = limpiar_y_extraer(detalles, "P1")
            p2 = limpiar_y_extraer(detalles, "P2") or p1
            p3 = limpiar_y_extraer(detalles, "P3") or p2
            e1 = limpiar_y_extraer(detalles, "E1")
            e2 = limpiar_y_extraer(detalles, "E2") or e1
            e3 = limpiar_y_extraer(detalles, "E3") or e2
            
            # Lógica especial para FV: acepta "FV" o "FV.EXC" pero NO "FBS"
            # Buscamos FV o FV.EXC explícitamente
            regex_fv = r"(?:FV|FV\.EXC).*?[:\s]+([\d]+[\.,][\d]+)"
            match_fv = re.search(regex_fv, detalles, re.IGNORECASE)
            fv = float(match_fv.group(1).replace(',', '.')) if match_fv else 0.0
            
            datos_finales.append({
                "Tarifa": tarifa, "P1": p1, "P2": p2, "P3": p3,
                "E1": e1, "E2": e2, "E3": e3, "FV": fv
            })

    df_final = pd.DataFrame(datos_finales)
    st.dataframe(df_final, use_container_width=True)
    
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar CSV", csv, "tarifas_finales.csv", "text/csv")
