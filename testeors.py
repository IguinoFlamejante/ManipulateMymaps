import openrouteservice
from openrouteservice import convert
import simplekml
from chaves import ORS_API_KEY
# Substitua pela sua chave da ORS
API_KEY = ORS_API_KEY

# Inicializa cliente
client = openrouteservice.Client(key=API_KEY)

# Lista de coordenadas [(lon, lat), ...]
coordenadas = [(-54.585, -25.520), (-54.575, -25.515), (-54.560, -25.510)]

# Solicita rota entre os pontos (modo carro)
rota = client.directions(coordinates=coordenadas, profile='driving-car')

# Decodifica a rota em lista de coordenadas
linha = convert.decode_polyline(rota['routes'][0]['geometry'])['coordinates']

# Salva em KML
kml = simplekml.Kml()
kml.newlinestring(name="Rota via ORS", coords=linha)
kml.save("rota_ors.kml")
print("✅ KML salvo: rota_ors.kml")
