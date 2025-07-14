import easyocr
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pdf2image import convert_from_path
import os

# Configurações
PASTA_ENTRADA = "./Entrada"
PASTA_SAIDA = "./Saida"
PASTA_RESULTADO = "./Resultado"
os.makedirs(PASTA_RESULTADO, exist_ok=True)
os.makedirs(PASTA_SAIDA, exist_ok=True)
POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"  # ajuste para seu poppler
DPI = 300

def processar_pagina(imagem_pil):
    # Converter PIL para OpenCV BGR
    img_cv = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

    # Detectar linhas
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=50, maxLineGap=10)

    img_linhas = img_rgb.copy()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(img_linhas, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # OCR com EasyOCR
    reader = easyocr.Reader(['pt'], gpu=False)
    resultados = reader.readtext(img_rgb)

    for (bbox, texto, conf) in resultados:
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple(map(int, top_left))
        bottom_right = tuple(map(int, bottom_right))
        cv2.rectangle(img_linhas, top_left, bottom_right, (255, 0, 0), 2)
        cv2.putText(img_linhas, texto, (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    return img_linhas, resultados

def pdf_para_imagem():
    for arquivo in os.listdir(PASTA_ENTRADA):
        if arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(PASTA_ENTRADA, arquivo)
            print(f"Convertendo {arquivo} em imagens...")
            paginas = convert_from_path(caminho_pdf, dpi=DPI, poppler_path=POPPLER_PATH)
            for i, pagina in enumerate(paginas):
                print(f"Processando página {i+1}/{len(paginas)}...")
                img_processada, textos = processar_pagina(pagina)

                print("Textos detectados:")
                for _, texto, conf in textos:
                    print(f"  {texto} ({conf:.2f})")

                plt.figure(figsize=(15,10))
                plt.imshow(img_processada)
                plt.axis('off')
                plt.title(f'Página {i+1} - Linhas (verde) + OCR (azul)')
                plt.show()
        else:
            print("Não é pdf!")

if __name__ == "__main__":
    pdf_para_imagem()
