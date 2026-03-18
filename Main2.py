import requests
import re
import json
import pandas as pd

def scraper_tarifas():
    url = "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    print("Iniciando extracción de 70+ tarifas...")
    res = requests.get(url, headers=headers)
    
    # Extraer el JSON oculto en la variable JS 'tarifas_bd'
    match = re.search(r'var\s+tarifas_bd\s*=\s*(\{.*?\});', res.text, re.DOTALL)
    if not match:
        return "No se pudo encontrar la base de datos."

    datos_raw = json.loads(match.group(1))
    lista_final = []

    for id_t, info in datos_raw.items():
        # Extraer valores base
        p1 = pd.to_numeric(info.get('p1'), errors='coerce')
        p2 = pd.to_numeric(info.get('p2'), errors='coerce')
        e1 = pd.to_numeric(info.get('e1'), errors='coerce')
        e2 = pd.to_numeric(info.get('e2'), errors='coerce')
        e3 = pd.to_numeric(info.get('e3'), errors='coerce')
        fv = pd.to_numeric(info.get('fvexc'), errors='coerce')

        # LÓGICA DE RELLENO SOLICITADA:
        # 1. Si E2 o E3 están vacíos, copiar E1
        val_e2 = e2 if pd.notnull(e2) else e1
        val_e3 = e3 if pd.notnull(e3) else e1
        
        # 2. Si FV está vacío, poner 0
        val_fv = fv if pd.notnull(fv) else 0.0

        fila = {
            'Compañía': info.get('cia'),
            'Tarifa': info.get('nom'),
            'P1_eur_kw_dia': p1,
            'P2_eur_kw_dia': p2,
            'E1_eur_kwh': e1,
            'E2_eur_kwh': val_e2,
            'E3_eur_kwh': val_e3,
            'FV_Excedentes': val_fv
        }
        lista_final.append(fila)

    df = pd.DataFrame(lista_final)
    
    # Guardar resultados
    df.to_csv('tarifas_luz_completo.csv', index=False, encoding='utf-8-sig')
    df.to_excel('tarifas_luz_completo.xlsx', index=False)
    
    print(f"Proceso finalizado. {len(df)} tarifas guardadas.")
    return df

if __name__ == "__main__":
    scraper_tarifas()
