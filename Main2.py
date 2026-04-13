import streamlit as st
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Tarifas Luz", layout="wide")
st.title("📊 Extractor de Tarifas de Luz - Debug")

def extraer_precio(texto, patron):
    # Patrón más robusto: busca el campo, cualquier texto (.*?), y luego el número
    # Esto captura formatos como "FV: 0,05", "FV - 0,05", "FV (exc): 0,05"
    regex = f"{patron}.*?([\d,]+)"
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        # Extraemos el grupo, limpiamos y convertimos
        valor = match.group(1).replace(',', '.')
        return float(valor)
    return None

# ... (función obtener_datos igual que antes)

if st.button('Generar Tabla con Depuración'):
    df = obtener_datos()
    datos_finales = []
    
    for _, fila in df.iterrows():
        tarifa = str(fila.iloc[2])
        detalles = str(fila.iloc[3])
        
        if tarifa != 'None' and 'Potencia' in detalles:
            # DEBUG: Muestra lo que estamos leyendo
            # st.write(f"Leyendo tarifa: {tarifa} | Detalles: {detalles[:50]}...")
            
            p1 = extraer_precio(detalles, "P1")
            p2 = extraer_precio(detalles, "P2") or p1
            p3 = extraer_precio(detalles, "P3") or p2
            e1 = extraer_precio(detalles, "E1")
            e2 = extraer_precio(detalles, "E2") or e1
            e3 = extraer_precio(detalles, "E3") or e2
            
            # Captura especial para FV
            fv = extraer_precio(detalles, "FV") or 0.0
            
            datos_finales.append({
                "Tarifa": tarifa, "P1": p1, "P2": p2, "P3": p3,
                "E1": e1, "E2": e2, "E3": e3, "FV": fv
            })
            
    st.dataframe(pd.DataFrame(datos_finales), use_container_width=True)
