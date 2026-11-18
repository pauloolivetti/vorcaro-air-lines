"""
VORCARO AIR LINES - backend
Lê o grafo do PostgreSQL/PostGIS e encontra a rota com o algoritmo de Dijkstra.
"""
import os
import psycopg2
from flask import Flask, jsonify, request, send_from_directory

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vorcaro:vorcaro@localhost:5432/vorcaro")
PRECO_POR_KM = 0.50       # R$ por km voado
VELOCIDADE_KMH = 800      # velocidade média do avião

app = Flask(__name__, static_folder="public", static_url_path="")


def carregar_grafo():
    """Monta o grafo como LISTA DE ADJACÊNCIA: { 'GRU': {'GIG': 343.2, ...}, ... }"""
    with psycopg2.connect(DATABASE_URL) as con, con.cursor() as cur:
        cur.execute("""SELECT iata, cidade, pais, ST_Y(geom::geometry), ST_X(geom::geometry)
                       FROM aeroporto ORDER BY cidade""")
        aeroportos = {iata: {"iata": iata, "cidade": cidade, "pais": pais, "lat": lat, "lng": lng}
                      for iata, cidade, pais, lat, lng in cur.fetchall()}

        cur.execute("SELECT origem, destino, distancia_km FROM rota_com_distancia")
        grafo = {iata: {} for iata in aeroportos}
        for origem, destino, km in cur.fetchall():
            grafo[origem][destino] = float(km)
    return aeroportos, grafo


def dijkstra(grafo, origem, destino):
    """Retorna (caminho, distância total) do menor caminho entre origem e destino."""
    distancia = {v: float("inf") for v in grafo}   # melhor distância conhecida
    anterior = {v: None for v in grafo}            # de onde eu vim (p/ remontar o caminho)
    distancia[origem] = 0
    nao_visitados = set(grafo)

    while nao_visitados:
        # 1) pega o vértice não visitado com a MENOR distância
        atual = min(nao_visitados, key=lambda v: distancia[v])
        if distancia[atual] == float("inf") or atual == destino:
            break
        nao_visitados.remove(atual)

        # 2) RELAXA as arestas: tenta melhorar a distância dos vizinhos
        for vizinho, peso in grafo[atual].items():
            nova = distancia[atual] + peso
            if nova < distancia[vizinho]:
                distancia[vizinho] = nova
                anterior[vizinho] = atual

    if distancia[destino] == float("inf"):
        return None, None

    # 3) remonta o caminho andando de trás pra frente
    caminho, v = [], destino
    while v is not None:
        caminho.insert(0, v)
        v = anterior[v]
    return caminho, distancia[destino]


@app.get("/")
def index():
    return send_from_directory("public", "index.html")


@app.get("/api/mapa")
def mapa():
    aeroportos, grafo = carregar_grafo()
    rotas = [[o, d, km] for o in grafo for d, km in grafo[o].items() if o < d]
    return jsonify(aeroportos=list(aeroportos.values()), rotas=rotas)


@app.get("/api/rota")
def rota():
    origem, destino = request.args.get("origem"), request.args.get("destino")
    aeroportos, grafo = carregar_grafo()
    if origem not in grafo or destino not in grafo:
        return jsonify(erro="Aeroporto inválido"), 400

    caminho, km = dijkstra(grafo, origem, destino)
    if caminho is None:
        return jsonify(erro="Não existe rota entre esses aeroportos"), 404

    trechos = [{"de": a, "para": b, "km": grafo[a][b]} for a, b in zip(caminho, caminho[1:])]
    return jsonify(
        caminho=[aeroportos[i] for i in caminho],
        trechos=trechos,
        distancia_km=round(km, 1),
        custo_reais=round(km * PRECO_POR_KM, 2),
        tempo_horas=round(km / VELOCIDADE_KMH, 2),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
