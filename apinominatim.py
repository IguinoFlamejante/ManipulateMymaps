import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

geolocator = Nominatim(user_agent="pdf_kml_extractor", timeout=10)

def get_bounding_box(cidade, estado="PR", pais="Brasil"):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": f"{cidade}, {estado}, {pais}", "format": "json", "limit": 1
    }
    headers = {"User-Agent": "pdf_kml_extractor"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if not data:
        print("⚠️ Cidade não encontrada.")
        return None

    bbox = data[0]["boundingbox"]  # normalmente: [sul, norte, oeste, leste]
    print(f"📦 Bounding Box para {cidade}:")
    print(f"Sul:   {bbox[0]}")
    print(f"Norte: {bbox[1]}")
    print(f"Oeste: {bbox[2]}")
    print(f"Leste: {bbox[3]}")

    # Converte para float e monta uma lista [oeste, sul, leste, norte]
    oeste = float(bbox[2])
    sul = float(bbox[0])
    leste = float(bbox[3])
    norte = float(bbox[1])

    viewbox = [oeste, sul, leste, norte]
    return viewbox


def ponto_dentro_viewbox(lat, lon, viewbox):
    min_lon, min_lat, max_lon, max_lat = viewbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def geocodificar(texto, viewbox):
    try:
        geolocator = Nominatim(user_agent="pdf_kml_extractor")
        if viewbox:
            oeste, sul, leste, norte = viewbox
            box_tuple = ((oeste, norte), (leste, sul))  # atenção: lat invertido!
            return geolocator.geocode(texto, viewbox=box_tuple, exactly_one=True, timeout=10)
        else:
            return geolocator.geocode(texto, exactly_one=True, timeout=10)
    except GeocoderTimedOut:
        return None
