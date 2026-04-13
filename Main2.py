import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas Profesional", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formato Maestro")

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
    response = requests.get(url, headers=headers, timeout=20)
    # Seleccionamos la primera tabla y nos aseguramos de que sea un DataFrame
    tablas = pd.read_html(io.StringIO(response.text))
    return tablas[0] if tablas else pd.DataFrame()

def limpiar_y_extraer(texto, patron):
    """Extrae números de forma segura. Si falla algo, devuelve 0.0"""
    try:
        texto_str = str(texto)
        # Regex que busca el patrón y captura el número (soporta 0,123 y 0.123)
        regex = f"{patron}.*?[:\s]+([\d]+[\.,][\d]+)"
        match = re.search(regex, texto_str, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(',', '.')
            return float(num_str)
    except:
        pass
    return 0.0

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

def to_xml(df):
    xml = ['<Tarifas>']
    for _, row in df.iterrows():
        xml.append('  <Tarifa>')
        for col in df.columns:
            # Usamos el nombre del segundo nivel de la columna para el tag
            tag_name = str(col[1]).replace(" ", "_").replace("á", "a").replace("ñ", "n").replace("í", "i").replace("(", "").replace(")", "").replace("/", "")
            xml.append(f'    <{tag_name}>{row[col]}</{tag_name}>')
        xml.append('  </Tarifa>')
    xml.append('</Tarifas>')
    return '\n'.join(xml)

if st.button('Generar Tabla Completa'):
    try:
        df_web = obtener_datos()
        if df_web.empty:
            st.error("No se pudieron obtener datos de la web.")
            st.stop()

        datos_finales = []
        
        for _, fila in df_web.iterrows():
            # Ignorar filas cortas o vacías
            if len(fila) < 4: continue
            
            # Extraer nombre y detalles de forma segura
            val_compania = fila.iloc[2]
            val_detalles = fila.iloc[3]
            
            if pd.isna(val_compania) or pd.isna(val_detalles):
                continue

            compania = normalizar_con_db(val_compania)
            detalles = str(val_detalles)
            
            # --- FILTROS ---
            nombre_check = compania.lower()
            excluir = ["indexado", "3.0td", "bv", "estabanell", "bonpreu", "electra", "som", "pvpc", "suministradora"]
            if any(termino in nombre_check for termino in excluir):
                continue
            
            if 'Potencia' in detalles:
                # Extracción con backups de periodos
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2")
                if p2 == 0.0: p2 = p1
                
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2")
                if e2 == 0.0: e2 = e1
                
                e3 = limpiar_y_extraer(detalles, "E3")
                if e3 == 0.0: e3 = e2
                
                # Excedentes: buscamos el patrón específico
                fv = limpiar_y_extraer(detalles, "FV.EXC")
                
                datos_finales.append([compania, p1, p2, e1, e2, e3, fv])

        # --- CABECERAS MULTI-NIVEL (Idéntico a tu Excel original) ---
        columnas = pd.MultiIndex.from_tuples([
            ("", "Compañía suministradora"),
            ("Coste término de Potencia en €/kWdia", "Periodo Punta"),
            ("Coste término de Potencia en €/kWdia", "Periodo Valle"),
            ("Coste término de Energía en €/kWh", "Periodo Punta"),
            ("Coste término de Energía en €/kWh", "Periodo Llano"),
            ("Coste término de Energía en €/kWh", "Periodo Valle"),
            ("", "Precio Excedentes en €/kWh")
        ])

        df_final = pd.DataFrame(datos_finales, columns=columnas)
        
        if not df_final.empty:
            # Quitamos duplicados y reseteamos índice
            df_final = df_final.drop_duplicates().reset_index(drop=True)
            
            st.subheader("Vista previa de la tabla")
            st.dataframe(df_final, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # EXCEL CON XLSXWRITER PARA CELDAS COMBINADAS
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Tarifas')
                    workbook = writer.book
                    worksheet = writer.sheets['Tarifas']
                    
                    # Formato de visualización
                    worksheet.set_column(0, 0, 35)
                    worksheet.set_column(1, 5, 18)
                    worksheet.set_column(6, 6, 25)
                
                st.download_button(
                    label="📥 Descargar Excel (.xlsx)",
                    data=output.getvalue(),
                    file_name="tarifas_luz_maestro.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col2:
                xml_data = to_xml(df_final)
                st.download_button("📑 Descargar XML", xml_data, "tarifas.xml", "application/xml")
            
            with col3:
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("📄 Descargar CSV", csv, "tarifas.csv", "text/csv")
        else:
            st.warning("No se encontraron tarifas válidas con los filtros actuales.")
                
    except Exception as e:
        st.error(f"Error general en el proceso: {e}")
