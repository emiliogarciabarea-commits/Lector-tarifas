import streamlit as st
import pandas as pd
import json
from playwright.sync_api import sync_playwright

# Configuración de la página
st.set_page_config(page_title="Scraper Tarifas", layout="wide")
st.title("📊 Extractor de Tarifas de Luz")

def extraer_datos_con_playwright():
    with sync_playwright() as p:
        # Lanzar navegador en modo invisible
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Acceder a la web
        page.goto("https://www.simuladorfacturaluz.es/tarifas-de-luz/", wait_until="networkidle")
        
        # Extraer el valor de la variable JavaScript del navegador
        # Esto es más efectivo que regex cuando el contenido es dinámico
        data = page.evaluate("window.tarifas_bd")
        browser.close()
        return data

def procesar_datos(tarifas_dict):
    datos_limpios = []
    
    def to_f(val):
        try: return float(str(val).replace(',', '.'))
        except: return 0.0

    for key, t in tarifas_dict.items():
        p1 = to_f(t.get('p1', 0))
        datos_limpios.append({
            'Compania': str(t.get('cia', 'S/D')).strip(),
            'Tarifa': str(t.get('nom', 'S/D')).strip(),
            'P1': p1,
            'P2': to_f(t.get('p2', p1)),
            'E1': to_f(t.get('e1', 0)),
            'E2': to_f(t.get('e2', t.get('e1', 0))),
            'E3': to_f(t.get('e3', t.get('e1', 0))),
            'FV': to_f(t.get('fvexc', 0))
        })
    return pd.DataFrame(datos_limpios)

# Interfaz
if st.button('Obtener Tarifas Actualizadas'):
    with st.spinner('Navegando y extrayendo datos...'):
        try:
            datos_raw = extraer_datos_con_playwright()
            if datos_raw:
                df = procesar_datos(datos_raw)
                st.success(f"Éxito: {len(df)} tarifas encontradas.")
                st.dataframe(df, use_container_width=True)
                
                # Botón descarga
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar CSV", csv, "tarifas_luz.csv", "text/csv")
            else:
                st.error("No se pudo extraer la información. El sitio web podría estar bloqueando el acceso.")
        except Exception as e:
            st.error(f"Error técnico: {e}")
        
        # Botón de descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV", csv, "tarifas.csv", "text/csv")
