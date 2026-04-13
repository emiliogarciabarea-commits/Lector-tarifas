import streamlit as st
import pandas as pd
import requests
import io
import re

# Configuración de página
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
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        tablas = pd.read_html(io.StringIO(response.text))
        return tablas[0] if tablas else pd.DataFrame()
    except Exception as e:
        st.error(f"Error al conectar con la web: {e}")
        return pd.DataFrame()

def extraer_numero_seguro(texto, patron):
    """Extrae el número del patrón. Si no existe o falla, devuelve 0.0 sin romper el código."""
    if not texto or pd.isna(texto):
        return 0.0
    try:
        # Busca el patrón y captura el número (soporta 0,123 y 0.123)
        regex = f"{patron}.*?[:\s]+([\d]+[\.,][\d]+)"
        match = re.search(regex, str(texto), re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '.'))
    except:
        pass
    return 0.0

def normalizar_con_db(nombre_web):
    nombre_web = " ".join(str(nombre_web).split())
    palabras_web = nombre_web.lower().split()[:3]
    inicio_web = " ".join(palabras_web)
    for nombre_limpio in DB_NOMBRES:
        palabras_db = nombre_limpio.lower().split()[:3]
        if inicio_web == " ".join(palabras_db):
            return nombre_limpio
    return re.split(r'\d{2}\s\w{3}\s\d{4}', nombre_web)[0].strip()

if st.button('🚀 Generar Tabla de Tarifas'):
    df_web = obtener_datos()
    
    if not df_web.empty:
        datos_procesados = []
        
        for _, fila in df_web.iterrows():
            # Saltamos filas que no tengan el mínimo de columnas
            if len(fila) < 4: continue
            
            val_compania = fila.iloc[2]
            val_detalles = fila.iloc[3]
            
            # Saltamos si son nulos o no es una tarifa real (debe contener 'Potencia')
            if pd.isna(val_compania) or pd.isna(val_detalles) or 'potencia' not in str(val_detalles).lower():
                continue

            compania = normalizar_con_db(val_compania)
            detalles = str(val_detalles)
            
            # Filtros de exclusión
            excluir = ["indexado", "3.0td", "bv", "estabanell", "bonpreu", "electra", "som", "pvpc", "suministradora"]
            if any(term in compania.lower() for term in excluir):
                continue
            
            # EXTRACCIÓN BLINDADA
            p1 = extraer_numero_seguro(detalles, "P1")
            p2 = extraer_numero_seguro(detalles, "P2")
            if p2 == 0.0: p2 = p1 # Caso tarifas de 1 solo periodo
            
            e1 = extraer_numero_seguro(detalles, "E1")
            e2 = extraer_numero_seguro(detalles, "E2")
            if e2 == 0.0: e2 = e1
            
            e3 = extraer_numero_seguro(detalles, "E3")
            if e3 == 0.0: e3 = e2
            
            fv = extraer_numero_seguro(detalles, "FV.EXC")
            
            datos_procesados.append([compania, p1, p2, e1, e2, e3, fv])

        # DEFINICIÓN DE CABECERAS (Idéntico a tu Excel original)
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
            st.subheader("📋 Tarifas Extraídas")
            st.dataframe(df_final, use_container_width=True)
            
            # BOTÓN DE DESCARGA EXCEL PROFESIONAL
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Tarifas')
                # Formateo automático de columnas
                worksheet = writer.sheets['Tarifas']
                for i, col in enumerate(df_final.columns):
                    worksheet.set_column(i, i, 20)
            
            st.download_button(
                label="📥 Descargar Excel (.xlsx)",
                data=output.getvalue(),
                file_name="tarifas_luz_maestro.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No se encontraron tarifas válidas.")
    else:
        st.error("No se pudo obtener la tabla de la web.")
