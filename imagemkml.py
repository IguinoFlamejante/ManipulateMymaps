import os
import re
import numpy as np
import unicodedata
import shutil
import simplekml
import easyocr
from pdf2image import convert_from_path
from difflib import get_close_matches
from easyocr import Reader
import google.generativeai as genai

from chaves import GEMINI_API_KEY
from apinominatim import get_bounding_box, geocodificar, ponto_dentro_viewbox
from csvreferencias import carregar_lista_fixa

genai.configure(api_key=GEMINI_API_KEY)

# Configurações
PASTA_ENTRADA = "./Entrada"
PASTA_SAIDA = "./Saida"
PASTA_RESULTADO = "./Resultado"
POPPLER_PATH = r"C:\\poppler-24.08.0\\Library\\bin"

os.makedirs(PASTA_SAIDA, exist_ok=True)
os.makedirs(PASTA_RESULTADO, exist_ok=True)

# Inicializa EasyOCR (Português e Inglês)
reader = easyocr.Reader(['pt'], gpu=False)

def ocr_com_gemini(image_pil):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([
        "Extraia todo o texto legível da imagem. Não resuma, apenas transcreva o que estiver escrito. E, caso haja palavras sem sentido, converta para nomes de locais.",
        image_pil
    ])
    return response.text.strip()

def limpar_nome_local(nome):
    nome = unicodedata.normalize("NFKD", nome)
    nome = nome.encode("ASCII", "ignore").decode("ASCII")  # remove acentos
    nome = re.sub(r"[^a-zA-Z0-9\s]", "", nome)
    nome = re.sub(r"\s+", " ", nome)
    return nome.strip().lower()

def preprocessar_texto_ocr(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = re.sub(r"[|•¬“”‘’—=_~<>]+", " ", texto)
    texto = re.sub(r"[^\w\sáéíóúãõâêôçÁÉÍÓÚÃÕÂÊÔÇ]", " ", texto)
    texto = re.sub(r"\s{2,}", " ", texto)
    return texto.strip()

def extrair_candidatos(texto):
    regex = re.compile(
        r"\b(?:Rua|Av|Avenida|Col[eé]gio|Cl[ií]nica|Hospital|Igreja|Centro|Residencial|Edif[ií]cio|Shopping|Minist[eé]rio|Correios)\s+.{3,60}",
        re.IGNORECASE,
    )
    candidatos = regex.findall(texto)
    return list(set(c.strip() for c in candidatos))

def casar_com_referencias(candidatos, referencias, cutoff=0.7):
    """
    candidatos: lista de nomes extraídos do OCR
    referencias: dicionário {nome_normalizado: (lat, lon)}
    Retorna: lista de tuplas (nome_original, lat, lon)
    """
    resultados = []
    for cand in candidatos:
        nome_normalizado = limpar_nome_local(cand)
        possivel = get_close_matches(nome_normalizado, referencias.keys(), n=1, cutoff=cutoff)
        if possivel:
            nome = possivel[0]
            lat, lon = referencias[nome]
            resultados.append((cand.strip(), lat, lon))  # usa nome original do OCR
    return resultados

def processar_pdfs_para_cidade(cidade, estado):
    viewbox = get_bounding_box(cidade, estado)
    if not viewbox or len(viewbox) < 4:
        print("❌ Não foi possível obter o bounding box da cidade.")
        return

    referencias = carregar_lista_fixa(cidade, estado)

    for nome_arquivo in os.listdir(PASTA_ENTRADA):
        if nome_arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(PASTA_ENTRADA, nome_arquivo)
            print(f"\n📄 Convertendo {nome_arquivo} em imagens...")
            imagens = convert_from_path(caminho_pdf, dpi=300, poppler_path=POPPLER_PATH)

            texto_total = ""
            for i, img in enumerate(imagens, 1):
                print(f" 🖼️ Processando página {i}/{len(imagens)} com Gemini OCR...")
                texto_ocr = ocr_com_gemini(img)
                print(f"📝 OCR Gemini página {i}:\n{texto_ocr[:300]}")
                texto_total += preprocessar_texto_ocr(texto_ocr) + "\n"

            candidatos = extrair_candidatos(texto_total)
            print(f"🧲 Candidatos extraídos: {candidatos}")
            if not candidatos:
                print("⚠️ Nenhum local foi extraído do texto.")
            locais_validos = casar_com_referencias(candidatos, referencias)

            print(f"🔍 Locais detectados: {locais_validos}")

            coordenadas = []
            usados = set()
            for nome, lat, lon in locais_validos:
                usados.add(limpar_nome_local(nome))
                if ponto_dentro_viewbox(lat, lon, viewbox):
                    print(f"✅ {nome} → ({lat}, {lon}) [✔ da referência e dentro da cidade]")
                    coordenadas.append((lon, lat))
                else:
                    print(f"⚠️ {nome} → ({lat}, {lon}) está FORA da cidade [via referência]")
            nomes_referencias = set(referencias.keys())
            restantes = [c for c in candidatos if limpar_nome_local(c) not in nomes_referencias]
            for local in restantes:
                print(f"🔎 Buscando: {local} dentro de {cidade}")
                location = geocodificar(local, viewbox)
                if location:
                    lat, lon = location.latitude, location.longitude
                    if ponto_dentro_viewbox(lat, lon, viewbox):
                        print(f"✅ {local} → ({lat}, {lon}) [✔ geocodificado dentro da cidade]")
                        coordenadas.append((lon, lat))
                    else:
                        print(f"⚠️ {local} → ({lat}, {lon}) está FORA da cidade [via geocodificação]")
                else:
                    print(f"❌ Não encontrado: {local}")

            if coordenadas:
                kml = simplekml.Kml()
                for i, coord in enumerate(coordenadas, 1):
                    kml.newpoint(name=f"Ponto {i}", coords=[coord])
                nome_kml = os.path.splitext(nome_arquivo)[0] + "_ia.kml"
                caminho_kml = os.path.join(PASTA_RESULTADO, nome_kml)
                kml.save(caminho_kml)
                print(f"✅ KML salvo: {caminho_kml}")
            else:
                print("⚠️ Nenhum local pôde ser geocodificado.")

            shutil.move(caminho_pdf, os.path.join(PASTA_SAIDA, nome_arquivo))
            print(f"📦 PDF movido para Saida: {nome_arquivo}")
       

if __name__ == "__main__":
    cidade = input("Qual cidade? ").strip()
    estado = input("Sigla do estado (ex: PR): ").strip()
    processar_pdfs_para_cidade(cidade, estado)
