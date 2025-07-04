import os
import xml.etree.ElementTree as ET
import simplekml
import shutil
from divideporm import interpolate_points
import geopy

entrada = "./Entrada"
resultado = "./Resultado"
saida = "./Saida"

os.makedirs(resultado, exist_ok=True)
os.makedirs(saida, exist_ok=True)

ns = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2'
}

distancia_segmento_m = float(input("Quantos metros para cada segmento?\n"))

for nome_arquivo in os.listdir(entrada):
    if nome_arquivo.lower().endswith(".kml"):
        caminho_entrada = os.path.join(entrada, nome_arquivo)
        print(f"📂 Processando: {nome_arquivo}")

        tree = ET.parse(caminho_entrada)
        root = tree.getroot()

        kml_out = simplekml.Kml(name="Segmentos do trajeto")

        # Percorre todos os placemarks com LineString
        for placemark in root.findall('.//kml:Placemark', ns):
            name_elem = placemark.find('kml:name', ns)
            nome_placemark = name_elem.text if name_elem is not None else "Segmento"

            linestring = placemark.find('.//kml:LineString', ns)
            if linestring is not None:
                coords_text = linestring.find('kml:coordinates', ns)
                if coords_text is None:
                    continue

                coords_raw = coords_text.text.strip().split()
                coords = []
                for c in coords_raw:
                    parts = c.split(',')
                    # longitude, latitude, altitude (opcional)
                    if len(parts) >= 2:
                        lon, lat = float(parts[0]), float(parts[1])
                        coords.append((lon, lat))

                if len(coords) < 2:
                    print(f"⚠️ Linha com menos de 2 pontos: {nome_placemark}")
                    continue

                if distancia_segmento_m > 0:
                    coords_interpoladas = interpolate_points(coords, distancia_segmento_m)
                else:
                    coords_interpoladas = coords
                print(f"Original: {len(coords)} pontos, interpolado: {len(coords_interpoladas)} pontos")
                # Divide em segmentos
                for i in range(len(coords_interpoladas) - 1):
                    segmento_coords = [coords_interpoladas[i], coords_interpoladas[i + 1]]
                    seg_name = f"{nome_placemark} - Segmento {i+1}"
                    linha = kml_out.newlinestring(name=seg_name, coords=segmento_coords)
                    linha.style.linestyle.width = 4
                    linha.style.linestyle.color = simplekml.Color.red

        nome_saida = nome_arquivo.replace(".kml", "_segmentado.kml")
        caminho_resultado = os.path.join(resultado, nome_saida)
        kml_out.save(caminho_resultado)
        print(f"✅ Salvo segmentado: {nome_saida}")

        # Move o arquivo original para a pasta saida
        shutil.move(caminho_entrada, os.path.join(saida, nome_arquivo))
        print(f"✅ Movido original para Saida: {nome_arquivo}")
