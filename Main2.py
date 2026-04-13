import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Versión Sin Indexados")

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
            
            compania = str(fila.iloc[2])
            detalles = str(fila.iloc[3])
            
            # FILTRO: Si "Indexado" está en el nombre de la compañía, saltamos esta fila
            if "indexado" in compania.lower():
                continue
            
            if compania != 'nan' and 'Potencia' in detalles:
                # Extracción
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2") or p1
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2") or e1
                e3 = limpiar_y_extraer(detalles, "E3") or e2
                
                # Lógica FV
                match_fv = re.search(r"FV\.EXC:\s*([\d]+[\.,][\d]+)\s*€/kWh", detalles, re.IGNORECASE)
                fv = float(match_fv.group(1).replace(',', '.')) if match_fv else 0.0
                
                datos_finales.append({
                    "Compañía suministradora": compania,
                    "Potencia: Periodo Punta": p1,
                    "Potencia: Periodo Valle": p2,
                    "Energía: Periodo Punta": e1,
                    "Energía: Periodo Llano": e2,
                    "Energía: Periodo Valle": e3,
                    "Precio Excedentes (€/kWh)": fv
                })

        df_final = pd.DataFrame(datos_finales)
        
        # Eliminar fila 0 si existe
        if not df_final.empty:
            df_final = df_final.iloc[1:]
        
        st.dataframe(df_final, use_container_width=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV", csv, "tarifas_finales.csv", "text/csv")
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
