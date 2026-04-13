import streamlit as st
import pandas as pd
import requests

# Configuración de la página
st.set_page_config(page_title="Extractor Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def obtener_datos_limpios():
    # URL de la API identificada
    url = "https://www.simuladorfacturaluz.es/sfl_api/?func=get_html_tarifas_luz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # Intentamos obtener los datos. Si la API devuelve JSON, lo procesamos.
        # Si devuelve una estructura que requiere parsing manual:
        data = response.json()
        
        datos_finales = []
        
        for item in data:
            # Función para asegurar que el dato sea número o None
            def to_f(val):
                try: 
                    # Convertimos string tipo '0,12' a float 0.12
                    return float(str(val).replace(',', '.')) 
                except: 
                    return None

            p1 = to_f(item.get('p1'))
            e1 = to_f(item.get('e1'))

            # FILTRO: Solo añadimos si tiene P1 o E1 (esto elimina las filas "None" o vacías)
            if p1 is not None or e1 is not None:
                datos_finales.append({
                    'Compañía': item.get('cia', 'N/A'),
                    'Tarifa': item.get('nom', 'N/A'),
                    'P1': p1,
                    'P2': to_f(item.get('p2')),
                    'P3': to_f(item.get('p3')),
                    'E1': e1,
                    'E2': to_f(item.get('e2')),
                    'E3': to_f(item.get('e3')),
                    'FV': to_f(item.get('fvexc', 0))
                })
        
        return pd.DataFrame(datos_finales), None
    except Exception as e:
        return None, f"Error al procesar los datos: {str(e)}"

# Interfaz en Streamlit
if st.button('Obtener Tarifas Limpias'):
    with st.spinner('Extrayendo datos de la API...'):
        df, error = obtener_datos_limpios()
        
        if error:
            st.error(error)
        else:
            st.success(f"¡Se han cargado {len(df)} tarifas correctamente!")
            st.dataframe(df, use_container_width=True)
            
            # Botón para descargar CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name='tarifas_limpias.csv',
                mime='text/csv'
            )
