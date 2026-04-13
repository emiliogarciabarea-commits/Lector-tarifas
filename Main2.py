import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formato Excel Exacto")

# Base de datos de nombres extraída de tu Excel
DB_NOMBRES = [
    "Iberdrola Plan Online", "Iberdrola Plan Online 3 periodos", "Iberdrola Plan Más Ahorro",
    "Iberdrola Plan Estable", "Iberdrola Plan Verano", "Iberdrola Plan Solar",
    "Iberdrola Plan Ahorro Solar", "Iberdrola Plan Ahorro Inteligente",
    "Endesa Tarifa Fija 24H Online", "Endesa Tarifa Fija 24h Promo", "Endesa Tarifa Conecta Luz",
    "Endesa Conecta Luz 3 Periodos",
    "Endesa Tempo Happy 50Horas", "Endesa Tempo Happy Domingos", "Naturgy Uso Luz",
    "Naturgy Tarifa Noche", "Naturgy Solar", "Repsol Ahorro Plus", "Repsol Ahorro Potencia",
    "Repsol Tarifa Solar", "Repsol Tranquilísima", "TotalEnergies A tu Aire Siempre",
    "TotalEnergies A tu Aire Programa Tu Ahorro", "Plenitude Fácil", "Gana Energia Online",
    "Gana Energia Sin Líos"
]

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

def normalizar_con_db(nombre_web):
    nombre_web = " ".join(str(nombre_web).split())
    # Comparar primeras 3 palabras
    palabras_web = nombre_web.lower().split()[:3]
    inicio_web = " ".join(palabras_web)

    for nombre_limpio in DB_NOMBRES:
        palabras_db = nombre_limpio.lower().split()[:3]
        inicio_db = " ".join(palabras_db)
        if inicio_web == inicio_db:
            return nombre_limpio
    
    # Si no hay match, devolver nombre limpio sin fechas
    return re.split(r'\d{2}\s\w{3}\s\d{4}', nombre_web)[0].strip()

if st.button('Generar Tabla Completa'):
    try:
        df = obtener_datos()
        datos_finales = []
        
        for _, fila in df.iterrows():
            if len(fila) < 4: continue
            
            compania = normalizar_con_db(fila.iloc[2])
            detalles = str(fila.iloc[3])
            
            # Filtros requeridos
            if any(x in compania.lower() for x in ["indexado", "3.0td"]):
                continue
            
            if compania != 'nan' and 'Potencia' in detalles:
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2") or p1
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2") or e1
                e3 = limpiar_y_extraer(detalles, "E3") or e2
                
                match_fv = re.search(r"FV\.EXC:\s*([\d]+[\.,][\d]+)\s*€/kWh", detalles, re.IGNORECASE)
                fv = float(match_fv.group(1).replace(',', '.')) if match_fv else 0.0
                
                datos_finales.append({
                    "Compañía suministradora": compania,
                    "Periodo Punta": p1,
                    "Periodo Valle": p2,
                    "Periodo Punta ": e1, # Espacio para diferenciar columnas
                    "Periodo Llano": e2,
                    "Periodo Valle ": e3,
                    "Precio Excedentes en €/kWh": fv
                })

        df_final = pd.DataFrame(datos_finales)
        
        if not df_final.empty:
            df_final = df_final.iloc[1:].reset_index(drop=True)
            st.dataframe(df_final, use_container_width=True)
            
            # Generar Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Tarifas')
            
            st.download_button("📥 Descargar Excel Actualizado", output.getvalue(), 
                               "tarifas_actualizadas.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
