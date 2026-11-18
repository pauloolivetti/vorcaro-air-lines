"""
VORCARO AIR LINES - backend
Lê o grafo do PostgreSQL/PostGIS e encontra a rota com o algoritmo de Dijkstra.
"""
import os
import psycopg2
from flask import Flask, jsonify, request, send_from_directory

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vorcaro:vorcaro@localhost:5432/vorcaro")
VELOCIDADE_KMH = 800      # velocidade média do avião

# Cada tipo de passageiro dá um PESO diferente para a mesma aresta (km do PostGIS).
# O Dijkstra é o mesmo; só muda o peso.
PERFIS = {
    # Amigos do Vorcaro: cada voo pesa 1 -> menos escalas (km/1e6 só desempata pelo mais curto)
    "amigo": lambda km: 1 + km / 1_000_000,
    # Não-amigos: peso = preço da passagem econômica do trecho (voo longo é bem mais caro)
    "pobre": lambda km: 39 + 0.10 * km + 0.00004 * km ** 2,
}

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


def dijkstra(grafo, origem, destino, peso):
    """Retorna (caminho, custo total) do caminho de menor custo entre origem e destino.
    peso(km) diz quanto custa usar uma aresta de km quilômetros."""
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
        for vizinho, km in grafo[atual].items():
            nova = distancia[atual] + peso(km)
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
    perfil = request.args.get("perfil", "amigo")
    aeroportos, grafo = carregar_grafo()
    if origem not in grafo or destino not in grafo or perfil not in PERFIS:
        return jsonify(erro="Parâmetros inválidos"), 400

    caminho, custo = dijkstra(grafo, origem, destino, PERFIS[perfil])
    if caminho is None:
        return jsonify(erro="Não existe rota entre esses aeroportos"), 404

    trechos = [{"de": a, "para": b, "km": grafo[a][b]} for a, b in zip(caminho, caminho[1:])]
    km = sum(t["km"] for t in trechos)
    escalas = len(caminho) - 2
    if perfil == "amigo":
        preco = km * 2.00                      # jatinho: R$ 2,00 por km
        tempo = km / 900 + escalas * 0.5       # jatinho mais rápido, escala no lounge VIP
    else:
        preco = custo                          # o custo do Dijkstra já é o preço
        tempo = km / VELOCIDADE_KMH + escalas * 2   # 2h de espera em cada escala

    return jsonify(
        caminho=[aeroportos[i] for i in caminho],
        trechos=trechos,
        escalas=escalas,
        distancia_km=round(km, 1),
        custo_reais=round(preco, 2),
        tempo_horas=round(tempo, 2),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
