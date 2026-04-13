import requests
import re
import json
import pandas as pd
import sys

def scraper_tarifas():
    url = "https://www.simuladorfacturaluz.es/tarifas-de-luz/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    print("Conectando al sitio web...")
    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status() # Lanza error si la conexión falla (403, 404, etc)
        
        # Ajustamos el regex para que sea más tolerante a espacios/saltos de línea
        match = re.search(r'var\s+tarifas_bd\s*=\s*(\{[\s\S]*?\});', res.text)
        
        if not match:
            print("ERROR: No se pudo localizar la variable 'tarifas_bd' en el código fuente.")
            print("Posible causa: La web ha cambiado su estructura o requiere cookies de sesión.")
            return

        print("Datos encontrados. Procesando JSON...")
        tarifas_dict = json.loads(match.group(1))
        datos_limpios = []

        def to_f(val):
            if val is None or val == "" or str(val).lower() == "nan": return 0.0
            try:
                return float(str(val).replace(',', '.'))
            except:
                return 0.0

        for key, t in tarifas_dict.items():
            p1 = to_f(t.get('p1'))
            datos_limpios.append({
                'Compania': str(t.get('cia', 'S/D')).strip(),
                'Tarifa': str(t.get('nom', 'S/D')).strip(),
                'P1': p1,
                'P2': to_f(t.get('p2', p1)),
                'E1': to_f(t.get('e1')),
                'E2': to_f(t.get('e2', t.get('e1'))),
                'E3': to_f(t.get('e3', t.get('e1'))),
                'FV': to_f(t.get('fvexc', 0))
            })

        df = pd.DataFrame(datos_limpios)
        
        # Exportación
        df.to_csv('tarifas_luz.csv', index=False, sep=',', encoding='utf-8')
        df.to_excel('tarifas_luz.xlsx', index=False)

        print(f"Éxito: Se han procesado {len(df)} registros.")
        print(df.head(10).to_string())

    except Exception as e:
        print(f"Ocurrió un error inesperado: {str(e)}")
    
    input("\nPresiona ENTER para cerrar la aplicación...")

if __name__ == "__main__":
    scraper_tarifas()
