import requests
import re
import json
import pandas as pd
import os

def clean_value(val, default=0.0):
    """Convierte a float de forma segura."""
    try:
        if val is None or val == "" or str(val).lower() == "nan":
            return default
        # Limpiar símbolos si los hubiera
        num_str = str(val).replace('€', '').replace(',', '.').strip()
        return float(num_str)
    except:
        return default

def scraper_tarifas():
    url = "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    # User-Agent real para evitar bloqueos y que la pantalla no se quede en "negro"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print("🌐 Conectando con la web...")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        
        # Buscar la base de datos en el JS
        match = re.search(r'var\s+tarifas_bd\s*=\s*(\{.*?\});', res.text, re.DOTALL)
        if not match:
            print("❌ Error: No se encontró la variable 'tarifas_bd'.")
            return

        datos_raw = json.loads(match.group(1))
        lista_final = []

        for info in datos_raw.values():
            # Extraer y limpiar
            e1 = clean_value(info.get('e1'))
            e2 = clean_value(info.get('e2'), default=e1) # Si no hay E2, usa E1
            e3 = clean_value(info.get('e3'), default=e1) # Si no hay E3, usa E1
            fv = clean_value(info.get('fvexc'), default=0.0)

            fila = {
                'Compañía': info.get('cia', 'Desconocida'),
                'Tarifa': info.get('nom', 'Sin nombre'),
                'P1_€/kW_dia': clean_value(info.get('p1')),
                'P2_€/kW_dia': clean_value(info.get('p2')),
                'E1_€/kWh': e1,
                'E2_€/kWh': e2,
                'E3_€/kWh': e3,
                'FV_Excedentes': fv
            }
            lista_final.append(fila)

        # Crear DataFrame
        df = pd.DataFrame(lista_final)
        
        # Guardar archivos
        df.to_csv('tarifas_luz.csv', index=False, encoding='utf-8-sig')
        df.to_excel('tarifas_luz.xlsx', index=False)
        
        print(f"✅ ¡Éxito! Se han procesado {len(df)} tarifas.")
        print("📁 Archivos generados: tarifas_luz.csv y tarifas_luz.xlsx")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    scraper_tarifas()
