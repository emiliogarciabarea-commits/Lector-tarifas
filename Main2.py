import streamlit as st
import pandas as pd
import requests
import io
import re

# ... (Configuración y obtener_datos igual que antes)

def extraer_precio(texto, patron):
    # Patrón más flexible:
    # 1. Busca el nombre (patron)
    # 2. Permite cualquier cosa en medio (.*? )
    # 3. Busca el número (incluyendo posibles símbolos € o espacios)
    regex = f"{patron}.*?([\d]+(?:[\.,][\d]+)?)"
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

if st.button('Generar Tabla Formateada'):
    df = obtener_datos()
    datos_finales = []
    
    for _, fila in df.iterrows():
        tarifa = str(fila.iloc[2])
        detalles = str(fila.iloc[3])
        
        if tarifa != 'None' and 'Potencia' in detalles:
            # DEBUG: DESCOMENTA LA SIGUIENTE LÍNEA PARA VER QUÉ DETALLES LLEGAN
            # st.text(f"Analizando: {detalles}") 
            
            p1 = extraer_precio(detalles, "P1")
            p2 = extraer_precio(detalles, "P2") or p1
            p3 = extraer_precio(detalles, "P3") or p2
            e1 = extraer_precio(detalles, "E1")
            e2 = extraer_precio(detalles, "E2") or e1
            e3 = extraer_precio(detalles, "E3") or e2
            
            # Buscamos FV específicamente
            # A veces aparece como "Fv" o "FV"
            fv = extraer_precio(detalles, "Fv") or 0.0
            
            datos_finales.append({
                "Tarifa": tarifa, "P1": p1, "P2": p2, "P3": p3,
                "E1": e1, "E2": e2, "E3": e3, "FV": fv
            })
            
    df_final = pd.DataFrame(datos_finales)
    st.dataframe(df_final, use_container_width=True)
