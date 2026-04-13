import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas (Datos Seleccionados)")

def obtener_datos_limpios():
    # Usamos la misma URL que descubriste
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    }
    
    response = requests.get(url, headers=headers)
    
    # Esta API devuelve una estructura que podemos convertir a JSON
    # Si la API devuelve un JSON directamente, usamos response.json()
    # Si la API devuelve una respuesta estructurada, la procesamos:
    try:
        # Intentamos obtener el JSON que la web usa internamente
        data = response.json() 
    except:
        return None, "La API no devolvió datos en formato JSON."

    datos_finales = []
    
    # Mapeo manual de los campos que solicitaste
    for item in data:
        datos_finales.append({
            'Compañía': item.get('cia', 'N/A'),
            'Tarifa': item.get('nom', 'N/A'),
            'P1': item.get('p1', 0),
            'P2': item.get('p2', 0),
            'P3': item.get('p3', 0),
            'E1': item.get('e1', 0),
            'E2': item.get('e2', 0),
            'E3': item.get('e3', 0),
            'FV': item.get('fvexc', 0)
        })
        
    return pd.DataFrame(datos_finales), None

if st.button('Obtener Mis Datos'):
    df, error = obtener_datos_limpios()
    if error:
        st.error(error)
    else:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV", csv, "tarifas_seleccionadas.csv", "text/csv")
