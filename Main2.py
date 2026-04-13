import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Filtro Estricto")

# Base de datos extraída de tu Excel
DB_NOMBRES = [
    "Iberdrola Plan Online", "Iberdrola Plan Online 3 periodos", "Iberdrola Plan Más Ahorro",
    "Iberdrola Plan Estable", "Iberdrola Plan Verano", "Iberdrola Plan Solar",
    "Iberdrola Plan Ahorro Solar", "Iberdrola Plan Ahorro Inteligente",
    "Endesa Tarifa Fija 24H Online", "Endesa Tarifa Fija 24h Promo", "Endesa Conecta",
    "Endesa One Luz", "Endesa One Luz 3 Periodos", "Endesa Tempo Happy 2Horas",
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
    palabras_web = nombre_web.lower().split()[:3]
    inicio_web = " ".join(palabras_web)

    for nombre_limpio in DB_NOMBRES:
        palabras_db = nombre_limpio.lower().split()[:3]
        inicio_db = " ".join(palabras_db)
        if inicio_web == inicio_db:
            return nombre_limpio
            
    return re.split(r'\d{2}\s\w{3}\s\d{4}', nombre_web)[0].strip()

if st.button('Generar Tabla Completa'):
    try:
        df = obtener_datos()
        datos_finales = []
        
        for _, fila in df.iterrows():
            if len(fila) < 4: continue
            
            # 1. Obtener nombre y limpiar
            compania = normalizar_con_db(fila.iloc[2])
            detalles = str(fila.iloc[3])
            
            # 2. FILTRO ESTRICTO: Si contiene "indexado", "3.0td" o "bv", se salta la fila
            # Se comprueba tanto en el nombre normalizado como en el original de la web
            nombre_raw = str(fila.iloc[2]).lower()
            nombre_norm = compania.lower()
            
            if any(term in nombre_raw or term in nombre_norm for term in ["indexado", "3.0td", "bv"]):
                continue
            
            if compania != 'nan' and 'Potencia' in detalles:
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2") or p1
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2") or e1
                e3 = limpiar_y_extraer(detalles, "E3") or e2
                
                match_fv = re.search(r"FV\.EXC:\s*([\d]+[\.,][\d]+)\s*€/kWh", detalles, re.IGNORECASE)
                fv = float(match_fv.group(1).replace(',', '.')) if match_fv else 0.0
                
                # Columnas alineadas con tu Excel
                datos_finales.append({
                    "Compañía suministradora": compania,
                    "Potencia Periodo Punta": p1,
                    "Potencia Periodo Valle": p2,
                    "Energía Periodo Punta": e1,
                    "Energía Periodo Llano": e2,
                    "Energía Periodo Valle": e3,
                    "Precio Excedentes (€/kWh)": fv
                })

        df_final = pd.DataFrame(datos_finales)
        
        if not df_final.empty:
            # Quitamos la primera fila si es basura y reseteamos el índice
            df_final = df_final.reset_index(drop=True)
            
            st.dataframe(df_final, use_container_width=True)
            
            # Exportación a Excel para mantener formato
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Tarifas Actualizadas')
            
            st.download_button(
                label="📥 Descargar Excel Final",
                data=output.getvalue(),
                file_name="tarifas_limpias.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Error en el proceso: {e}")
