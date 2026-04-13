import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Versión Final")

def obtener_datos():
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"}
    response = requests.get(url, headers=headers, timeout=20)
    return pd.read_html(io.StringIO(response.text))[0]

def limpiar_y_extraer(texto, patron):
    # Primero limpiamos el texto: quitamos '€', '/kWh', espacios raros
    texto_limpio = texto.replace('€', '').replace('/kWh', '').replace('≈', '')
    # Buscamos el patrón seguido de cualquier cosa y luego el número
    match = re.search(f"{patron}.*?([\d]+(?:[\.,][\d]+)?)", texto_limpio, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

if st.button('Generar Tabla Completa'):
    df = obtener_datos()
    datos_finales = []
    
    for _, fila in df.iterrows():
        tarifa = str(fila.iloc[2])
        detalles = str(fila.iloc[3])
        
        if tarifa != 'nan' and 'Potencia' in detalles:
            p1 = limpiar_y_extraer(detalles, "P1")
            p2 = limpiar_y_extraer(detalles, "P2") or p1
            p3 = limpiar_y_extraer(detalles, "P3") or p2
            e1 = limpiar_y_extraer(detalles, "E1")
            e2 = limpiar_y_extraer(detalles, "E2") or e1
            e3 = limpiar_y_extraer(detalles, "E3") or e2
            
            # Buscamos FV específicamente
            fv = limpiar_y_extraer(detalles, "FV") or 0.0
            
            datos_finales.append({
                "Tarifa": tarifa, "P1": p1, "P2": p2, "P3": p3,
                "E1": e1, "E2": e2, "E3": e3, "FV": fv
            })
            # DEBUG: Para saber qué lee, descomenta:
            # st.text(f"Tarifa: {tarifa} | FV encontrado: {fv}")

    df_final = pd.DataFrame(datos_finales)
    st.dataframe(df_final, use_container_width=True)
    
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar CSV", csv, "tarifas_finales.csv", "text/csv")
