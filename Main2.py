import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas Profesional", layout="wide")
st.title("📊 Extractor de Tarifas - Formato Excel Maestro")

# (La lista DB_NOMBRES y funciones auxiliares se mantienen igual)
DB_NOMBRES = [...] # (Tu lista completa aquí)

def to_xml(df):
    # XML ajustado para la estructura plana de los datos
    xml = ['<Tarifas>']
    for _, row in df.iterrows():
        xml.append('  <Tarifa>')
        # Convertimos las tuplas de MultiIndex a nombres de etiqueta simples
        for col_name, value in row.items():
            tag = str(col_name).replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
            xml.append(f'    <{tag}>{value}</{tag}>')
        xml.append('  </Tarifa>')
    xml.append('</Tarifas>')
    return '\n'.join(xml)

if st.button('Generar Excel Estructurado'):
    try:
        df = obtener_datos()
        datos_finales = []
        
        for _, fila in df.iterrows():
            if len(fila) < 4: continue
            
            compania = normalizar_con_db(fila.iloc[2])
            detalles = str(fila.iloc[3])
            
            # FILTROS
            if any(t in compania.lower() for t in ["indexado", "3.0td", "bv", "estabanell", "bonpreu", "electra", "som"]):
                continue
            
            if 'Potencia' in detalles:
                p1 = limpiar_y_extraer(detalles, "P1")
                p2 = limpiar_y_extraer(detalles, "P2") or p1
                e1 = limpiar_y_extraer(detalles, "E1")
                e2 = limpiar_y_extraer(detalles, "E2") or e1
                e3 = limpiar_y_extraer(detalles, "E3") or e2
                fv = limpiar_y_extraer(detalles, "FV.EXC") or 0.0
                
                datos_finales.append({
                    "Compañía": compania,
                    "Pot_Punta": p1, "Pot_Valle": p2,
                    "En_Punta": e1, "En_Llano": e2, "En_Valle": e3,
                    "Exc": fv
                })

        df_temp = pd.DataFrame(datos_finales)
        
        # --- CREACIÓN DEL MULTIINDEX PARA EL EXCEL ---
        df_final = pd.DataFrame(
            data=df_temp.values,
            columns=pd.MultiIndex.from_tuples([
                ("", "Compañía suministradora"),
                ("Coste término de Potencia en €/kWdia", "Periodo Punta"),
                ("Coste término de Potencia en €/kWdia", "Periodo Valle"),
                ("Coste término de Energía en €/kWh", "Periodo Punta"),
                ("Coste término de Energía en €/kWh", "Periodo Llano"),
                ("Coste término de Energía en €/kWh", "Periodo Valle"),
                ("", "Precio Excedentes en €/kWh")
            ])
        )
        
        # Guardar en Excel con MultiIndex
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)
            
        st.dataframe(df_final, use_container_width=True)
        st.download_button("📥 Descargar Excel Formateado", output.getvalue(), "tarifas_maestro.xlsx")
            
    except Exception as e:
        st.error(f"Error técnico: {e}")
