import os
import xml.etree.ElementTree as ET
import simplekml
from geopy.distance import geodesic
from collections import defaultdict
import shutil

entrada = "./Entrada"
resultado = "./Resultado"
saida = "./Saida"

os.makedirs(resultado, exist_ok=True)
os.makedirs(saida, exist_ok=True)

ns = {'kml': 'http://www.opengis.net/kml/2.2'}

def distancia(p1, p2):
    return geodesic((p1[1], p1[0]), (p2[1], p2[0])).meters

def remover_repetidos(pontos, tolerancia=1):
    if not pontos:
        return []
    filtrados = [pontos[0]]
    for pt in pontos[1:]:
        if distancia(pt, filtrados[-1]) > tolerancia:
            filtrados.append(pt)
    return filtrados

def construir_trilhas_conectadas(segmentos, tolerancia=10):
    trilhas = []
    usados = set()

    for i, seg in enumerate(segmentos):
        if i in usados:
            continue
        trilha = list(seg)
        usados.add(i)

        mudou = True
        while mudou:
            mudou = False
            for j, outro in enumerate(segmentos):
                if j in usados:
                    continue
                if distancia(trilha[-1], outro[0]) <= tolerancia:
                    trilha.extend(outro[1:])
                    usados.add(j)
                    mudou = True
                elif distancia(trilha[0], outro[-1]) <= tolerancia:
                    trilha = outro[:-1] + trilha
                    usados.add(j)
                    mudou = True
        trilhas.append(remover_repetidos(trilha))
    return trilhas

for nome_arquivo in os.listdir(entrada):
    if not nome_arquivo.lower().endswith(".kml"):
        continue

    caminho_entrada = os.path.join(entrada, nome_arquivo)
    print(f"📂 Lendo: {nome_arquivo}")
    tree = ET.parse(caminho_entrada)
    root = tree.getroot()

    segmentos_por_nome = defaultdict(list)

    for placemark in root.findall('.//kml:Placemark', ns):
        name_elem = placemark.find('kml:name', ns)
        nome_completo = name_elem.text.strip() if name_elem is not None else "Sem nome"
        nome_base = nome_completo.split(" - Segmento")[0].strip()

        coords_elem = placemark.find('.//kml:coordinates', ns)
        if coords_elem is not None:
            coords_raw = coords_elem.text.strip().split()
            coords = []
            for c in coords_raw:
                parts = c.split(',')
                if len(parts) >= 2:
                    lon, lat = float(parts[0]), float(parts[1])
                    coords.append((lon, lat))
            if len(coords) >= 2:
                segmentos_por_nome[nome_base].append(coords)

    if not segmentos_por_nome:
        print("⚠️ Nenhum placemark com coordenadas encontrado.")
        continue

    kml_out = simplekml.Kml()

    for nome_linha, segmentos in segmentos_por_nome.items():
        trilhas = construir_trilhas_conectadas(segmentos)

        for idx, trilha in enumerate(trilhas, 1):
            if len(trilha) < 2:
                continue
            linha = kml_out.newlinestring(
                name=f"{nome_linha} - Rota {idx}",
                coords=trilha
            )
            linha.style.linestyle.width = 4
            linha.style.linestyle.color = simplekml.Color.blue

    caminho_saida = os.path.join(resultado, nome_arquivo.replace(".kml", "_unido.kml"))
    kml_out.save(caminho_saida)
    print(f"✅ Salvo: {caminho_saida}")
    shutil.move(caminho_entrada, os.path.join(saida, nome_arquivo))
    print(f"📦 Movido para Saida: {nome_arquivo}")
