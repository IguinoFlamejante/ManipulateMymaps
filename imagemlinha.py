import os
import cv2
import numpy as np
import simplekml
import shutil
from pdf2image import convert_from_path
from PIL import Image
from apinominatim import get_bounding_box
import re

# Configurações de pastas
POPPLER_PATH = r"C:\\poppler-24.08.0\\Library\\bin"
PASTA_ENTRADA = "./Entrada"
PASTA_TEMP = "./Temp"
PASTA_SAIDA = "./Saida"
PASTA_RESULTADO = "./Resultado"

# Garante que as pastas existam
os.makedirs(PASTA_ENTRADA, exist_ok=True)
os.makedirs(PASTA_TEMP, exist_ok=True)
os.makedirs(PASTA_SAIDA, exist_ok=True)
os.makedirs(PASTA_RESULTADO, exist_ok=True)

def limpar_nome_arquivo(nome):
    return re.sub(r"[^\w\d_-]+", "_", nome)

def extrair_linha_do_mapa(imagem_path):
    img = cv2.imread(imagem_path)
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, binarizada = cv2.threshold(cinza, 50, 255, cv2.THRESH_BINARY_INV)

    kernel = np.ones((3,3), np.uint8)
    abertura = cv2.morphologyEx(binarizada, cv2.MORPH_OPEN, kernel, iterations=2)

    contornos, _ = cv2.findContours(abertura, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pontos = []
    for contorno in contornos:
        for p in contorno:
            x, y = p[0]
            pontos.append((x, y))

    if not pontos:
        print("⚠️ Nenhuma linha detectada.")
        return []

    print(f"✅ {len(pontos)} pontos extraídos da linha.")
    return pontos

def converter_pixel_para_latlon(pontos_pixel, bounds_img, bbox_geografico):
    largura, altura = bounds_img
    oeste, leste, sul, norte = bbox_geografico

    coordenadas = []
    for x, y in pontos_pixel:
        lon = oeste + (x / largura) * (leste - oeste)
        lat = sul + ((altura - y) / altura) * (norte - sul)
        coordenadas.append((lon, lat))
    return coordenadas

def gerar_kml_trajeto(coordenadas, caminho_kml):
    kml = simplekml.Kml()
    kml.newlinestring(name="Trajeto detectado", coords=coordenadas)
    kml.save(caminho_kml)
    print(f"✅ KML salvo em: {caminho_kml}")

def processar_pdf_para_trajeto(caminho_pdf, bbox_geografico):
    nome_arquivo = os.path.basename(caminho_pdf)
    nome_base, _ = os.path.splitext(nome_arquivo)
    nome_limpo = limpar_nome_arquivo(nome_base)
    imagem_temp_path = os.path.join(PASTA_TEMP, "pagina_temp.png")
    caminho_kml = os.path.join(PASTA_RESULTADO, f"{nome_base}_trajeto.kml")
    print(f"📄 Convertendo PDF: {nome_arquivo}")
    imagens = convert_from_path(caminho_pdf, dpi=300, poppler_path=POPPLER_PATH)
    if not imagens:
        print(f"❌ Nenhuma imagem gerada do PDF: {caminho_pdf}")
        return
    imagem = imagens[0].convert("RGB")
    imagem.save(imagem_temp_path)
    print(f"✅ Imagem salva em: {imagem_temp_path}")
    if not os.path.exists(imagem_temp_path):
        print(f"❌ Imagem não foi salva: {imagem_temp_path}")
        return
    pontos_pixel = extrair_linha_do_mapa(imagem_temp_path)
    if not pontos_pixel:
        return

    largura, altura = imagem.size
    coordenadas_geo = converter_pixel_para_latlon(pontos_pixel, (largura, altura), bbox_geografico)

    gerar_kml_trajeto(coordenadas_geo, caminho_kml)

    # Mover PDF para pasta de saída
    novo_caminho_pdf = os.path.join(PASTA_SAIDA, nome_arquivo)
    shutil.move(caminho_pdf, novo_caminho_pdf)
    print(f"📦 PDF movido para: {novo_caminho_pdf}")

def limpar_pasta_temp():
    for arquivo in os.listdir(PASTA_TEMP):
        caminho = os.path.join(PASTA_TEMP, arquivo)
        if os.path.isfile(caminho):
            os.remove(caminho)

if __name__ == "__main__":
    cidade = input("🌍 Cidade (ex: Foz do Iguaçu): ").strip()
    estado = input("📍 Sigla do estado (ex: PR): ").strip()

    bbox = get_bounding_box(cidade, estado)  # (Sul, Norte, Oeste, Leste)
    if not bbox:
        print("❌ Bounding box não encontrado.")
    else:
        bbox_reordenado = (bbox[2], bbox[3], bbox[0], bbox[1])  # Oeste, Leste, Sul, Norte
        pdfs = [f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith(".pdf")]

        if not pdfs:
            print("⚠️ Nenhum PDF encontrado em ./Entrada.")
        else:
            limpar_pasta_temp()
            for nome_pdf in pdfs:
                caminho_pdf = os.path.join(PASTA_ENTRADA, nome_pdf)
                processar_pdf_para_trajeto(caminho_pdf, bbox_reordenado)
