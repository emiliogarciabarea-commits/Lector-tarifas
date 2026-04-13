import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas Maestro", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formato Profesional")

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
    try:
        response = requests.get(url, headers=headers, timeout=20)
        tablas = pd.read_html(io.StringIO(response.text))
        return tablas[0] if tablas else pd.DataFrame()
    except:
        return pd.DataFrame()

def extraer_numero_seguro(texto, patron):
    try:
        if not texto or pd.isna(texto): return 0.0
        match = re.search(f"{patron}.*?(\d+[\.,]\d+)", str(texto), re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '.'))
    except:
        pass
    return 0.0

def normalizar_nombre(nombre_raw):
    nombre_limpio = " ".join(str(nombre_raw).split()).strip()
    nombre_limpio = re.split(r'\d{2}\s\w{3}\s\d{4}', nombre_limpio)[0].strip()
    for db_n in DB_NOMBRES:
        if db_n.lower() in nombre_limpio.lower() or nombre_limpio.lower() in db_n.lower():
            return db_n
    return nombre_limpio

if st.button('🚀 Generar Tabla y Archivos'):
    df_web = obtener_datos()
    
    if not df_web.empty:
        datos_procesados = []
        for _, fila in df_web.iterrows():
            if len(fila) < 4: continue
            compania_raw = fila.iloc[2]
            detalles = str(fila.iloc[3])
            
            if "potencia" not in detalles.lower(): continue

            #nombre_final = normalizar_nombre(compania_raw)
            excluir = ["indexado", "3.0td", "bv", "estabanell", "bonpreu", "electra", "som", "pvpc", "bonpreuplan"]
            if any(palabra in detalles.lower() for palabra in excluir):
                continue
            nombre_final = normalizar_nombre(compania_raw)
            
            p1 = extraer_numero_seguro(detalles, "P1")
            p2 = extraer_numero_seguro(detalles, "P2") or p1
            e1 = extraer_numero_seguro(detalles, "E1")
            e2 = extraer_numero_seguro(detalles, "E2") or e1
            e3 = extraer_numero_seguro(detalles, "E3") or e2
            fv = extraer_numero_seguro(detalles, "FV.EXC")
            
            datos_procesados.append([nombre_final, p1, p2, e1, e2, e3, fv])

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
            st.success(f"¡Se han extraído {len(df_final)} tarifas!")
            st.dataframe(df_final, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                output_excel = io.BytesIO()
                # Aplanamos columnas para que Excel no falle
                df_excel = df_final.copy()
                df_excel.columns = [f"{c[0]} {c[1]}".strip() for c in df_excel.columns]
                
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    df_excel.to_excel(writer, index=False, sheet_name='Tarifas')
                
                st.download_button("📥 Descargar Excel (.xlsx)", output_excel.getvalue(), "tarifas_luz.xlsx")

            with col2:
                buffer_txt = io.StringIO()
                buffer_txt.write("LISTADO DE TARIFAS ELÉCTRICAS\n" + "="*40 + "\n\n")
                buffer_txt.write(df_final.to_string(index=False))
                st.download_button("📄 Descargar Documento de Texto (.txt)", buffer_txt.getvalue(), "tarifas_luz.txt")
        else:
            st.warning("No se encontraron tarifas válidas.")
    else:
        st.error("No se pudo conectar con la fuente de datos.")
