import os
import csv
import time
import re
import unicodedata
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII','ignore').decode().strip().lower()

def extrair_coordenadas_da_url(url):
    m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)

def obter_sigla_estado(sigla_ou_nome):
    resp = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados")
    for e in resp.json():
        if normalizar(sigla_ou_nome) in (normalizar(e['sigla']), normalizar(e['nome'])):
            return e['sigla']
    return None

def cidade_existe(cidade, uf):
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
    resp = requests.get(url)
    return any(normalizar(m['nome']) == normalizar(cidade) for m in resp.json())

def buscar_coordenadas(cidade, estado_input):
    uf = obter_sigla_estado(estado_input)
    if not uf:
        print(f"❌ Estado inválido: {estado_input}")
        return
    if not cidade_existe(cidade, uf):
        print(f"❌ Cidade '{cidade}' não encontrada em {uf}")
        return

    ent = os.path.join("Referencias", "entrada_locais.csv")
    sai = os.path.join("Referencias", "Cidades", f"{normalizar(cidade)}{uf}.csv")
    os.makedirs(os.path.dirname(sai), exist_ok=True)

    # Carrega já existentes
    vistos = set()
    if os.path.exists(sai):
        with open(sai,newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r.get("Latitude") and r.get("Longitude"):
                    vistos.add(normalizar(r["Nome"]))

    # Ler arquivo de entrada
    with open(ent,newline='', encoding='utf-8') as f:
        ler = csv.DictReader(f, delimiter=';')
        nomes = [r["Nome"].strip() for r in ler if r.get("Nome","").strip()]

    # Selenium
    opts = Options()
    opts.add_argument('--headless')
    driver = webdriver.Chrome(options=opts)

    novos = []
    for nome in nomes:
        nn = normalizar(nome)
        if nn in vistos:
            print(f"⏭️  Já consta: {nome}")
            continue
        driver.get(f"https://www.google.com/maps/search/{nome} {cidade} {uf}".replace(" ","+"))
        time.sleep(3)
        lat, lon = extrair_coordenadas_da_url(driver.current_url)
        novos.append({"Nome": nome, "Latitude": lat or "", "Longitude": lon or ""})
        print(f"{'✅' if lat else '❌'} {nome} → {lat},{lon}")

    driver.quit()
    if not novos:
        print("✔️ Sem novos locais para salvar.")
        return

    # Grava resultados
    cab = not os.path.exists(sai)
    with open(sai, "a", newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["Nome","Latitude","Longitude"])
        if cab: w.writeheader()
        w.writerows(novos)

    print(f"📁 Salvou {len(novos)} itens em {sai}")


def carregar_lista_fixa(cidade, estado):
    uf = obter_sigla_estado(estado)
    if not uf:
        print(f"❌ Estado inválido: {estado}")
        return
    if not cidade_existe(cidade, uf):
        print(f"❌ Cidade '{cidade}' não encontrada em {uf}")
        return
    nome_arquivo = f"{normalizar(cidade)}{uf}.csv"
    caminho = os.path.join("Referencias", "Cidades", nome_arquivo)
    referencias = {}
    if os.path.exists(caminho):
        with open(caminho, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat = float(row["Latitude"])
                    lon = float(row["Longitude"])
                    nome = normalizar(row["Nome"])
                    referencias[nome] = (lat, lon)
                except:
                    continue
    return referencias

if __name__ == "__main__":
    buscar_coordenadas("Foz do Iguaçu", "PR")