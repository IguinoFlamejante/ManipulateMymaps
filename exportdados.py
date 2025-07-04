import os
from fastkml import kml
import shutil
import xml.etree.ElementTree as ET
# Caminho da pasta com arquivos KML
entrada = ".\Entrada"
saida = ".\Saida"

ns = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2'
}

# Percorre todos os arquivos da pasta
for nome_arquivo in os.listdir(entrada):
    if nome_arquivo.lower().endswith('.kml'):
        caminho_arquivo = os.path.join(entrada, nome_arquivo)
        tree = ET.parse(caminho_arquivo)
        root = tree.getroot()
        for placemark in root.findall('.//kml:Placemark', ns):
            name = placemark.find('kml:name', ns)
            linestring = placemark.find('.//kml:LineString', ns)
            if linestring is not None:
                coords = linestring.find('kml:coordinates', ns).text.strip().split()
                print(f"Placemark: {name.text if name is not None else 'sem nome'}, Coordenadas:")
                for c in coords:
                    print(" ", c)

        with open(caminho_arquivo, "rb") as f:  # <-- Modo binário aqui
            doc = f.read()

        k = kml.KML()
        k.from_string(doc)  # agora funciona com bytes

        print(f"\n📂 Arquivo: {nome_arquivo}")
        for feature in k.features:
            for placemark in feature.features():
                print("  🏷️ Nome:", placemark.name)
                print("  📍 Geometria:", placemark.geometry)
        caminho_destino = os.path.join(saida, nome_arquivo)
        shutil.move(caminho_arquivo, caminho_destino)
        print(f"✅ Movido: {nome_arquivo}")
        