import simplekml

kml_out = simplekml.Kml(name="Exemplo")

# Adiciona duas linhas de exemplo
kml_out.newlinestring(name="Segmento 1", coords=[(-54.5873, -20.4642), (-54.5867, -20.4645)])
kml_out.newlinestring(name="Segmento 2", coords=[(-54.5867, -20.4645), (-54.5860, -20.4648)])

kml_out.save("exemplo_segmentado.kml")