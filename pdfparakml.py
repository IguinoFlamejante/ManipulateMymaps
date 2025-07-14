import pdfplumber
import re
import simplekml
import os
import xml.etree.ElementTree as ET
import shutil

#Se no pdf tiver as coordenadas, não se for só uma imagem

entrada = "./Entrada"
resultado = "./Resultado"
saida = "./Saida"

os.makedirs(resultado, exist_ok=True)
os.makedirs(saida, exist_ok=True)

ns = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2'
}

pattern = re.compile(r"ll=(-?\d+\.\d+),(-?\d+\.\d+)")
pattern_latlon = re.compile(r"(-?\d{2,3}\.\d+),\s*(-?\d{2,3}\.\d+)")

coords_encontradas = []

for nome_arquivo in os.listdir(entrada):
    if nome_arquivo.lower().endswith(".pdf"):
        caminho_arquivo = os.path.join(entrada, nome_arquivo)
        with pdfplumber.open(caminho_arquivo) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    matches_links = pattern.findall(text)
                    matches_coords = pattern_latlon.findall(text)

                    for lat, lon in matches_links:
                        coords_encontradas.append((float(lon), float(lat)))

                    for lat, lon in matches_coords:
                        coords_encontradas.append((float(lon), float(lat)))
                if hasattr(page, "hyperlinks"):
                    for link in page.hyperlinks:
                        href = link.get("uri")
                        if href:
                            matches = pattern.findall(href)
                            for lat, lon in matches:
                                coords_encontradas.append((float(lon), float(lat)))
        print("🔍 Coordenadas extraídas:")
        for coord in coords_encontradas:
            print(coord)
        if coords_encontradas:
            kml = simplekml.Kml()
            linha = kml.newlinestring(name="Rota Extraída", coords=coords_encontradas)
            linha.style.linestyle.width = 4
            linha.style.linestyle.color = simplekml.Color.red
            nome_kml = os.path.splitext(nome_arquivo)[0] + ".kml"
            caminho_kml = os.path.join(resultado, nome_kml)
            kml.save(caminho_kml)
            print(f"✅ KML salvo como {caminho_kml}")
        else:
            print("⚠️ Nenhuma coordenada encontrada no PDF.")
        shutil.move(caminho_arquivo, os.path.join(saida, nome_arquivo))
        print(f"📦 PDF movido para Saida: {nome_arquivo}")
    else:
        print(f"❌ Ignorado (não é PDF): {nome_arquivo}")