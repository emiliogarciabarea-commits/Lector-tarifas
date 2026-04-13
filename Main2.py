import streamlit as st
import pandas as pd
import requests
import json
import re

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def obtener_datos():
    url = "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    # Headers para hacerse pasar por un navegador Chrome real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, f"Error HTTP {response.status_code}"
        
        # Buscar la variable en el texto
        match = re.search(r'var\s+tarifas_bd\s*=\s*(\{[\s\S]*?\});', response.text)
        if not match:
            return None, "No se encontraron datos en el código fuente."
            
        return json.loads(match.group(1)), None
    except Exception as e:
        return None, str(e)

if st.button('Obtener Tarifas Actualizadas'):
    with st.spinner('Conectando...'):
        data, error = obtener_datos()
        
        if error:
            st.error(f"Error: {error}")
        else:
            # Procesar datos
            datos_limpios = []
            for key, t in data.items():
                def to_f(val):
                    try: return float(str(val).replace(',', '.'))
                    except: return 0.0
                
                datos_limpios.append({
                    'Compania': str(t.get('cia', 'S/D')),
                    'Tarifa': str(t.get('nom', 'S/D')),
                    'P1': to_f(t.get('p1', 0)),
                    'P2': to_f(t.get('p2', 0)),
                    'E1': to_f(t.get('e1', 0)),
                    'E2': to_f(t.get('e2', 0)),
                    'E3': to_f(t.get('e3', 0)),
                    'FV': to_f(t.get('fvexc', 0))
                })
            
            df = pd.DataFrame(datos_limpios)
            st.success("¡Datos cargados con éxito!")
            st.dataframe(df)
            
            # Botón descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", csv, "tarifas_luz.csv", "text/csv")
