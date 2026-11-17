# 🎤 Colinha para a apresentação

## 1. O problema
Uma companhia aérea tem aeroportos e voos entre eles. Dado uma **origem** e um
**destino**, queremos a rota de **menor custo**, e o custo é proporcional à distância.

## 2. Modelagem como grafo
- **Vértices** = aeroportos (tabela `aeroporto`, com a localização em `GEOGRAPHY(POINT)`).
- **Arestas** = voos cadastrados (tabela `rota`, cada voo tem ida e volta).
- **Peso** = distância real em km, calculada pelo PostGIS:

```sql
ST_Distance(origem.geom, destino.geom) / 1000   -- metros → km
```

Usamos o tipo `GEOGRAPHY`, então o PostGIS mede a distância sobre a curvatura da
Terra (elipsoide WGS 84), e não em linha reta num plano.

No Python o grafo vira uma **lista de adjacência** (dicionário de dicionários):

```python
{ 'GRU': {'GIG': 343.2, 'MIA': 6553.6, ...},
  'MIA': {'GRU': 6553.6, 'GCM': 728.5, ...}, ... }
```

## 3. Algoritmo de Dijkstra (função `dijkstra` em `app.py`)
1. Toda distância começa em **infinito**, menos a origem, que começa em **0**.
2. Enquanto houver vértices não visitados:
   - pega o **não visitado com menor distância** (esse já é definitivo);
   - para cada vizinho, **relaxa** a aresta: se `dist[atual] + peso < dist[vizinho]`,
     atualiza a distância e guarda `anterior[vizinho] = atual`.
3. Para quando o destino é escolhido (já é o menor caminho possível).
4. Remonta o caminho voltando pelo vetor `anterior`, do destino até a origem.

**Por que funciona?** Os pesos são distâncias, logo **nunca negativos**. Então quando
um vértice é o menor da fila, nenhum outro caminho pode chegar nele mais barato depois.

**Complexidade:** escolhemos o menor com uma busca linear, então é **O(V²)**,
ótimo para ~30 aeroportos. Com uma fila de prioridade (heap) seria **O((V+E) log V)**.

## 4. Exemplo para mostrar ao vivo
**São Paulo (GRU) → Ilhas Cayman (GCM)**: não existe voo direto, o Dijkstra
encontra **GRU → MIA → GCM**, com ~7.282 km, R$ 3.641 e ~9h de voo.

**Porto Alegre (POA) → Fernando de Noronha (FEN)**: POA → GRU → SSA → REC → FEN.

## 5. Saída do sistema
O mapa desenha a rota e o cartão de embarque mostra o caminho, cada trecho,
a **distância total**, o **custo total (R$)** e o **tempo total de voo**.
