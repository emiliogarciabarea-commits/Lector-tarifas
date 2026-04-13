import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Versión Excel Match")

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
    # 1. Limpieza básica de espacios y saltos de línea
    nombre_limpio = " ".join(str(nombre).split())
    
    # 2. Cortar fechas (ej: 31 Mar 2026)
    nombre_limpio = re.split(r'\d{2}\s\w{3}\s\d{4}', nombre_limpio)[0].strip()
    
    # 3. MAPEO ESPECÍFICO PARA TU EXCEL
    # Aquí añadimos las reglas para que coincida exactamente con tus nombres
    reemplazos = {
        "Naturgy Por Uso": "Naturgy Uso Luz",
        "Naturgy Tarifa Uso Luz": "Naturgy Uso Luz",
        "TotalEnergies A Tu Aire Siempre": "TotalEnergies A tu Aire Siempre",
        "Gana Energía": "Gana Energia",
        "Endesa Tarifa Conecta": "Endesa Conecta",
        # Puedes añadir aquí cualquier otro que veas diferente
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
            
            compania_raw = str(fila.iloc[2])
            compania = normalizar_nombre(compania_raw)
            detalles = str(fila.iloc[3])
            
            # FILTRO: Si "Indexado" está en el nombre, saltamos
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
        
        if not df_final.empty:
            # Quitamos la fila 0 de la extracción web
            df_final = df_final.iloc[1:].reset_index(drop=True)
        
        st.dataframe(df_final, use_container_width=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV", csv, "tarifas_finales.csv", "text/csv")
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
