import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Versión a Prueba de Fallos")

def extraer_valor(texto, etiqueta):
    # Busca la etiqueta, ignora el texto intermedio, y captura el número decimal
    # El patrón [0-9]+[.,][0-9]+ asegura que SOLO coja números con decimales
    regex = f"{etiqueta}.*?[:\s]+([0-9]+[.,][0-9]+)"
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return 0.0

if st.button('Generar Tabla'):
    try:
        url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=20)
        df = pd.read_html(io.StringIO(response.text))[0]
        
        datos_limpios = []
        
        # Iteramos fila a fila
        for _, fila in df.iterrows():
            # Convertimos toda la fila a texto para evitar errores de tipo
            texto_fila = " ".join([str(x) for x in fila.values])
            
            # Buscamos solo filas que tengan "Potencia"
            if "Potencia" in texto_fila:
                # Extraemos datos uno a uno
                p1 = extraer_valor(texto_fila, "P1")
                p2 = extraer_valor(texto_fila, "P2") or p1
                p3 = extraer_valor(texto_fila, "P3") or p2
                e1 = extraer_valor(texto_fila, "E1")
                e2 = extraer_valor(texto_fila, "E2") or e1
                e3 = extraer_valor(texto_fila, "E3") or e2
                
                # Para FV: buscamos FV o FV.EXC pero nos detenemos si viene FBS
                # Cortamos el texto en FBS para que el buscador de FV no vea nada después
                texto_corto = re.split(r'FBS', texto_fila, flags=re.IGNORECASE)[0]
                fv = extraer_valor(texto_corto, "FV(?:\.EXC)?")
                
                datos_limpios.append({
                    "Tarifa": str(fila.iloc[2]), 
                    "P1": p1, "P2": p2, "P3": p3,
                    "E1": e1, "E2": e2, "E3": e3, "FV": fv
                })
        
        # Creamos el DataFrame final
        df_final = pd.DataFrame(datos_limpios)
        st.dataframe(df_final, use_container_width=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV", csv, "tarifas.csv", "text/csv")
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
