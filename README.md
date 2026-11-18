# ✈️ Vorcaro Air Lines — Sistema de Rotas Aéreas (PRJ.ED.18)

Sistema que desenha rotas de uma companhia aérea (fictícia e satírica) em um mapa.
As rotas ficam salvas em um **grafo** no **PostgreSQL + PostGIS**, o custo de cada
rota é a **distância real** entre as cidades (latitude/longitude) e o caminho é
encontrado com o **algoritmo de Dijkstra**, implementado na mão.

## Estrutura

```
vorcaro-air-lines/
├── db/init.sql          ← tabelas, aeroportos reais, rotas e a view com ST_Distance
├── app.py               ← backend: lê o grafo do banco + Dijkstra + API
├── public/index.html    ← tela com o mapa (Leaflet) e o design da companhia
├── docker-compose.yml   ← sobe o PostgreSQL com PostGIS já configurado
├── requirements.txt
└── APRESENTACAO.md      ← colinha pra explicar pro professor
```

## Como rodar (3 comandos)

Pré-requisitos: **Docker** e **Python 3.10+**.

```bash
# 1) sobe o banco PostGIS (cria as tabelas e os dados sozinho na 1ª vez)
docker compose up -d

# 2) instala as dependências do Python
pip install -r requirements.txt

# 3) roda o sistema
python app.py
```

Abra **http://localhost:5000**, escolha origem e destino e clique em **DECOLAR!**

> Se o `python app.py` der erro de conexão, espere uns 10 segundos: o banco ainda está iniciando.
> Pra recriar o banco do zero: `docker compose down -v && docker compose up -d`.

### Sem Docker?

Instale o PostgreSQL com a extensão PostGIS, crie um banco e rode o script:

```bash
createdb vorcaro
psql -d vorcaro -f db/init.sql
DATABASE_URL="postgresql://SEU_USUARIO:SUA_SENHA@localhost:5432/vorcaro" python app.py
```

## Publicar na internet (Vercel + Neon)

A Vercel roda o `app.py` (Flask) sozinha, mas não tem PostgreSQL próprio com PostGIS.
Usamos o **Neon** (Postgres grátis na nuvem, com suporte a PostGIS).

1. **Banco:** crie uma conta em https://neon.tech, crie um projeto e abra o **SQL Editor**.
   Cole todo o conteúdo de `db/init.sql` e clique em **Run**.
2. Copie a **connection string** do Neon (algo como
   `postgresql://usuario:senha@ep-xxx.neon.tech/neondb?sslmode=require`).
3. **Deploy:** suba esta pasta para um repositório no GitHub e importe em
   https://vercel.com/new (ou rode `npx vercel` dentro da pasta).
4. Na Vercel, em **Settings → Environment Variables**, crie `DATABASE_URL`
   com a connection string do Neon e faça **Redeploy**.

## API

| Rota | O que faz |
|---|---|
| `GET /api/mapa` | Lista os aeroportos (vértices) e rotas (arestas) para desenhar o mapa |
| `GET /api/rota?origem=GRU&destino=GCM&perfil=amigo` | Roda o Dijkstra e devolve o caminho, os trechos, escalas, distância (km), preço (R$) e tempo (h). `perfil=amigo` (menos voos) ou `perfil=pobre` (mais barato) |
| `/bastidores.html` | Explicação didática em 8 etapas: grafo, árvore e Dijkstra passo a passo |

## Como o custo é calculado

A distância real de cada aresta (km) vem do PostGIS com `ST_Distance(geography, geography)`
(view `rota_com_distancia`). A partir dela, cada tipo de passageiro usa um peso:

- **Amigos do Vorcaro**: peso = 1 por voo (menos escalas). Preço = R$ 2,00/km.
- **Não-amigos**: peso = preço da passagem = 39 + 0,10·km + 0,00004·km². Voo longo fica caro, então vale fazer escalas.
- **Passageiro normal** (nos bastidores): peso = km, custo proporcional à distância.

Para cadastrar uma rota nova é só inserir no banco (ida e volta) e recarregar a página:

```sql
INSERT INTO rota VALUES ('FEN','NAT'), ('NAT','FEN');
```

---
*Vorcaro Air Lines é uma paródia feita para fins acadêmicos. Qualquer semelhança com
pessoas reais é caricatura e sátira.*
