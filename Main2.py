import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formato Excel Exacto")

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

def normalizar_nombre(nombre):
    nombre_limpio = " ".join(str(nombre).split())
    nombre_limpio = re.split(r'\d{2}\s\w{3}\s\d{4}', nombre_limpio)[0].strip()
    
    reemplazos = {
        "Naturgy Por Uso": "Naturgy Uso Luz",
        "Naturgy Tarifa Uso Luz": "Naturgy Uso Luz",
        "TotalEnergies A Tu Aire Siempre": "TotalEnergies A tu Aire Siempre",
        "Gana Energía": "Gana Energia",
        "Endesa Tarifa Conecta": "Endesa Conecta",
    }
    
    for original, destino in reemplazos.items():
        if original in nombre_limpio:
            return destino
    return nombre_limpio

if st.button('Generar Tabla Completa'):
    try:
        df = obtener_datos()
        datos_finales = []
        
        for _, fila in df.iterrows():
            if len(fila) < 4: continue
            
            compania = normalizar_nombre(str(fila.iloc[2]))
            detalles = str(fila.iloc[3])
            
            if "indexado" in compania.lower():
                continue
            
            if compania != 'nan' and 'Potencia' in detalles:
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2") or p1
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2") or e1
                e3 = limpiar_y_extraer(detalles, "E3") or e2
                
                match_fv = re.search(r"FV\.EXC:\s*([\d]+[\.,][\d]+)\s*€/kWh", detalles, re.IGNORECASE)
                fv = float(match_fv.group(1).replace(',', '.')) if match_fv else 0.0
                
                # NOMBRES DE COLUMNA EXACTOS AL EXCEL ADJUNTO
                datos_finales.append({
                    "Compañía suministradora": compania,
                    "Periodo Punta": p1, # Corresponde a Potencia
                    "Periodo Valle": p2, # Corresponde a Potencia
                    "Periodo Punta ": e1, # Espacio extra al final para diferenciar de Potencia
                    "Periodo Llano": e2,
                    "Periodo Valle ": e3, # Espacio extra al final
                    "Precio Excedentes en €/kWh": fv
                })

        df_final = pd.DataFrame(datos_finales)
        
        if not df_final.empty:
            df_final = df_final.iloc[1:].reset_index(drop=True)
            
            # Mostramos la tabla en la app
            st.dataframe(df_final, use_container_width=True)
            
            # LÓGICA PARA GENERAR EXCEL (.xlsx)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Tarifas')
                writer.close()
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Descargar Excel Actualizado",
                data=excel_data,
                file_name="tarifas_actualizadas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
