import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas Profesional", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Formato Original")

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

def to_xml(df):
    xml = ['<Tarifas>']
    for _, row in df.iterrows():
        xml.append('  <Tarifa>')
        for col in df.columns:
            # Usamos el nombre del segundo nivel para las etiquetas XML
            tag = str(col[1]).replace(" ", "_").replace("á", "a").replace("ñ", "n").replace("í", "i").replace("(", "").replace(")", "").replace("/", "")
            xml.append(f'    <{tag}>{row[col]}</{tag}>')
        xml.append('  </Tarifa>')
    xml.append('</Tarifas>')
    return '\n'.join(xml)

if st.button('Generar Tabla Completa'):
    try:
        df_web = obtener_datos()
        datos_finales = []
        
        for _, fila in df_web.iterrows():
            if len(fila) < 4: continue
            
            compania = normalizar_con_db(fila.iloc[2])
            detalles = str(fila.iloc[3])
            
            # --- SECCIÓN DE FILTROS ACTUALIZADA ---
            nombre_check = compania.lower()
            excluir = ["indexado", "3.0td", "bv", "estabanell", "bonpreu", "electra", "som"]
            
            if any(termino in nombre_check for termino in excluir):
                continue
            
            if compania != 'nan' and 'Potencia' in detalles:
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2") or p1
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2") or e1
                e3 = limpiar_y_extraer(detalles, "E3") or e2
                
                match_fv = re.search(r"FV\.EXC:\s*([\d]+[\.,][\d]+)\s*€/kWh", detalles, re.IGNORECASE)
                fv = float(match_fv.group(1).replace(',', '.')) if match_fv else 0.0
                
                datos_finales.append([compania, p1, p2, e1, e2, e3, fv])

        # --- ESTRUCTURA DE COLUMNAS DOBLES (Igual al adjunto) ---
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
            # Saltamos la primera fila basura de la web
            df_final = df_final.reset_index(drop=True)
            
            st.subheader("Vista previa de la tabla limpia")
            st.dataframe(df_final, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Exportar Excel (.xlsx)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False)
                st.download_button("📥 Descargar Excel (.xlsx)", output.getvalue(), "tarifas_limpias.xlsx")

            with col2:
                # Exportar XML
                xml_data = to_xml(df_final)
                st.download_button("📑 Descargar XML", xml_data, "tarifas.xml", "application/xml")
            
            with col3:
                # Exportar CSV original
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("📄 Descargar CSV", csv, "tarifas.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Error técnico: {e}")
