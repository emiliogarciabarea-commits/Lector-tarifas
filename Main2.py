import requests
import re
import json
import pandas as pd

def scraper_tarifas():
    url = "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print("Conectando...")
        res = requests.get(url, headers=headers, timeout=20)
        
        # Extraemos el bloque de datos
        match = re.search(r'var\s+tarifas_bd\s*=\s*(\{.*?\});', res.text, re.DOTALL)
        if not match:
            print("No se encontraron los datos en la web.")
            return

        tarifas_dict = json.loads(match.group(1))
        datos_limpios = []

        for key in tarifas_dict:
            t = tarifas_dict[key]
            
            # Limpieza de valores numéricos
            def to_f(val):
                if val is None or val == "" or str(val).lower() == "nan": return None
                return float(str(val).replace(',', '.'))

            # Obtener valores base
            p1 = to_f(t.get('p1', 0))
            p2 = to_f(t.get('p2', p1)) # Si P2 es nulo, usa P1
            e1 = to_f(t.get('e1', 0))
            e2 = to_f(t.get('e2', e1)) # REGLA: Si no hay E2, usa E1
            e3 = to_f(t.get('e3', e1)) # REGLA: Si no hay E3, usa E1
            fv = to_f(t.get('fvexc', 0)) # REGLA: Si no hay FV, usa 0

            datos_limpios.append({
                'Compania': str(t.get('cia', 'S/D')).strip(),
                'Tarifa': str(t.get('nom', 'S/D')).strip(),
                'P1': p1,
                'P2': p2,
                'E1': e1,
                'E2': e2,
                'E3': e3,
                'FV': fv
            })

        # Crear el DataFrame
        df = pd.DataFrame(datos_limpios)

        # 1. Guardar como CSV estándar (punto para decimales, coma para separar)
        df.to_csv('tarifas_luz.csv', index=False, sep=',', encoding='utf-8')
        
        # 2. Guardar como Excel
        df.to_excel('tarifas_luz.xlsx', index=False)

        print(f"Éxito: {len(df)} tarifas procesadas.")
        # Imprimimos las primeras 5 para verificar en el log de GitHub
        print(df.head().to_string())

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    scraper_tarifas()
