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
    regex = f"{patron}.*?[:\s]+([\d]+[\.,][\d]+)"
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

if st.button('Generar Tabla Completa'):
    try:
        df = obtener_datos()
        datos_finales = []
        
        for _, fila in df.iterrows():
            if len(fila) < 4: continue
            
            tarifa = str(fila.iloc[2])
            detalles = str(fila.iloc[3])
            
            if tarifa != 'nan' and 'Potencia' in detalles:
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2") or p1
                p3 = limpiar_y_extraer(detalles, "P3") or p2
                
                # LÓGICA: Si P3 == P2, guardamos None para que quede vacío
                p3_val = None if (p3 == p2) else p3
                
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2") or e1
                e3 = limpiar_y_extraer(detalles, "E3") or e2
                
                regex_fv = r"(?:FV\.EXC|FV).*?[:\s]+([\d]+[\.,][\d]+)(?=\s*.*FBS|$)"
                match_fv = re.search(regex_fv, detalles, re.IGNORECASE)
                fv = float(match_fv.group(1).replace(',', '.')) if match_fv else 0.0
                
                datos_finales.append({
                    "Tarifa": tarifa, "P1": p1, "P2": p2, "P3": p3_val,
                    "E1": e1, "E2": e2, "E3": e3, "FV": fv
                })

        df_final = pd.DataFrame(datos_finales)
        
        # ELIMINAR COLUMNA P3 SI ESTÁ VACÍA EN TODAS LAS FILAS
        if df_final['P3'].isna().all():
            df_final = df_final.drop(columns=['P3'])
            
        st.dataframe(df_final, use_container_width=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV", csv, "tarifas_finales.csv", "text/csv")
        
    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")
