import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas Maestro", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formato Profesional")

# Base de datos para normalización
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
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        tablas = pd.read_html(io.StringIO(response.text))
        return tablas[0] if tablas else pd.DataFrame()
    except:
        return pd.DataFrame()

def extraer_numero_seguro(texto, patron):
    """Extrae números de forma segura. Si el patrón no existe, devuelve 0.0."""
    try:
        if not texto or pd.isna(texto): return 0.0
        # Buscamos el patrón y capturamos el número siguiente
        match = re.search(f"{patron}.*?(\d+[\.,]\d+)", str(texto), re.IGNORECASE)
        return float(match.group(1).replace(',', '.')) if match else 0.0
    except:
        return 0.0

def normalizar_nombre(nombre_raw):
    nombre_limpio = " ".join(str(nombre_raw).split()).strip()
    return nombre_limpio

if st.button('🚀 Generar Tabla y Descargar'):
    with st.spinner('Procesando datos...'):
        df_web = obtener_datos()
        
        if not df_web.empty:
            datos_procesados = []
            
            for _, fila in df_web.iterrows():
                if len(fila) < 4: continue
                
                compania_raw = fila.iloc[2]
                detalles = str(fila.iloc[3])
                
                # Filtro de seguridad: solo procesamos filas con datos reales
                if "potencia" not in detalles.lower(): continue

                # Extracción segura de valores
                p1 = extraer_numero_seguro(detalles, "P1")
                p2 = extraer_numero_seguro(detalles, "P2") or p1
                e1 = extraer_numero_seguro(detalles, "E1")
                e2 = extraer_numero_seguro(detalles, "E2") or e1
                e3 = extraer_numero_seguro(detalles, "E3") or e2
                fv = extraer_numero_seguro(detalles, "FV\.EXC") # <--- BLINDADO AQUÍ
                
                datos_procesados.append([compania_raw, p1, p2, e1, e2, e3, fv])

            # Estructura MultiIndex
            columnas = pd.MultiIndex.from_tuples([
                ("", "Compañía suministradora"),
                ("Coste término de Potencia en €/kWdia", "Periodo Punta"),
                ("Coste término de Potencia en €/kWdia", "Periodo Valle"),
                ("Coste término de Energía en €/kWh", "Periodo Punta"),
                ("Coste término de Energía en €/kWh", "Periodo Llano"),
                ("Coste término de Energía en €/kWh", "Periodo Valle"),
                ("", "Precio Excedentes en €/kWh")
            ])

            df_final = pd.DataFrame(datos_procesados, columns=columnas)
            df_final = df_final.drop_duplicates().reset_index(drop=True)

            if not df_final.empty:
                st.dataframe(df_final, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                # Excel
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False)
                col1.download_button("📥 Descargar Excel", output_excel.getvalue(), "tarifas.xlsx")
                
                # Texto plano
                buffer_txt = io.StringIO()
                buffer_txt.write(df_final.to_string(index=False))
                col2.download_button("📄 Descargar TXT", buffer_txt.getvalue(), "tarifas.txt")
            else:
                st.warning("No se encontraron tarifas válidas.")
        else:
            st.error("No se pudieron obtener datos de la web.")
