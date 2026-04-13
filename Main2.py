import streamlit as st
import requests
import re
import json
import pandas as pd

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Simulador de Tarifas de Luz")

def cargar_datos():
    url = "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=20)
        match = re.search(r'var\s+tarifas_bd\s*=\s*(\{[\s\S]*?\});', res.text)
        
        if not match:
            return None, "No se encontraron los datos."
            
        tarifas_dict = json.loads(match.group(1))
        datos_limpios = []

        def to_f(val):
            try: return float(str(val).replace(',', '.'))
            except: return 0.0

        for key, t in tarifas_dict.items():
            p1 = to_f(t.get('p1'))
            datos_limpios.append({
                'Compania': str(t.get('cia', 'S/D')).strip(),
                'Tarifa': str(t.get('nom', 'S/D')).strip(),
                'P1': p1, 'P2': to_f(t.get('p2', p1)),
                'E1': to_f(t.get('e1')), 'E2': to_f(t.get('e2', t.get('e1'))),
                'E3': to_f(t.get('e3', t.get('e1'))), 'FV': to_f(t.get('fvexc', 0))
            })
        return pd.DataFrame(datos_limpios), None
    except Exception as e:
        return None, str(e)

# Botón para cargar
if st.button('Actualizar Tarifas'):
    df, error = cargar_datos()
    if error:
        st.error(f"Error: {error}")
    else:
        st.success("Datos cargados correctamente")
        st.dataframe(df) # Esto muestra la tabla interactiva
        
        # Botón de descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV", csv, "tarifas.csv", "text/csv")
