-- =============================================================
--  VORCARO AIR LINES  -  Banco de dados (PostgreSQL + PostGIS)
-- =============================================================
CREATE EXTENSION IF NOT EXISTS postgis;

-- VÉRTICES do grafo: aeroportos com latitude/longitude reais
CREATE TABLE aeroporto (
    iata   CHAR(3) PRIMARY KEY,
    cidade VARCHAR(60) NOT NULL,
    pais   VARCHAR(40) NOT NULL,
    geom   GEOGRAPHY(POINT, 4326) NOT NULL   -- ponto (longitude, latitude)
);

-- ARESTAS do grafo: rotas cadastradas (ida e volta)
CREATE TABLE rota (
    origem  CHAR(3) REFERENCES aeroporto(iata),
    destino CHAR(3) REFERENCES aeroporto(iata),
    PRIMARY KEY (origem, destino)
);

-- ATENÇÃO: ST_MakePoint recebe (LONGITUDE, LATITUDE), nessa ordem!
INSERT INTO aeroporto (iata, cidade, pais, geom) VALUES
 ('GRU','São Paulo','Brasil',          ST_MakePoint(-46.4731,-23.4356)::geography),
 ('GIG','Rio de Janeiro','Brasil',     ST_MakePoint(-43.2506,-22.8100)::geography),
 ('BSB','Brasília','Brasil',           ST_MakePoint(-47.9186,-15.8711)::geography),
 ('CNF','Belo Horizonte','Brasil',     ST_MakePoint(-43.9719,-19.6244)::geography),
 ('SSA','Salvador','Brasil',           ST_MakePoint(-38.3225,-12.9086)::geography),
 ('REC','Recife','Brasil',             ST_MakePoint(-34.9236, -8.1265)::geography),
 ('FOR','Fortaleza','Brasil',          ST_MakePoint(-38.5326, -3.7763)::geography),
 ('POA','Porto Alegre','Brasil',       ST_MakePoint(-51.1711,-29.9939)::geography),
 ('CWB','Curitiba','Brasil',           ST_MakePoint(-49.1758,-25.5285)::geography),
 ('FLN','Florianópolis','Brasil',      ST_MakePoint(-48.5525,-27.6703)::geography),
 ('MAO','Manaus','Brasil',             ST_MakePoint(-60.0497, -3.0386)::geography),
 ('BEL','Belém','Brasil',              ST_MakePoint(-48.4763, -1.3792)::geography),
 ('GYN','Goiânia','Brasil',            ST_MakePoint(-49.2207,-16.6320)::geography),
 ('CGB','Cuiabá','Brasil',             ST_MakePoint(-56.1167,-15.6529)::geography),
 ('CGR','Campo Grande','Brasil',       ST_MakePoint(-54.6725,-20.4687)::geography),
 ('NAT','Natal','Brasil',              ST_MakePoint(-35.3761, -5.7681)::geography),
 ('MCZ','Maceió','Brasil',             ST_MakePoint(-35.7917, -9.5108)::geography),
 ('VIX','Vitória','Brasil',            ST_MakePoint(-40.2864,-20.2581)::geography),
 ('SLZ','São Luís','Brasil',           ST_MakePoint(-44.2341, -2.5854)::geography),
 ('THE','Teresina','Brasil',           ST_MakePoint(-42.8235, -5.0599)::geography),
 ('PVH','Porto Velho','Brasil',        ST_MakePoint(-63.9023, -8.7093)::geography),
 ('FEN','Fernando de Noronha','Brasil',ST_MakePoint(-32.4233, -3.8549)::geography),
 ('IGU','Foz do Iguaçu','Brasil',      ST_MakePoint(-54.4850,-25.6003)::geography),
 ('EZE','Buenos Aires','Argentina',    ST_MakePoint(-58.5358,-34.8222)::geography),
 ('SCL','Santiago','Chile',            ST_MakePoint(-70.7858,-33.3930)::geography),
 ('MIA','Miami','EUA',                 ST_MakePoint(-80.2870, 25.7959)::geography),
 ('JFK','Nova York','EUA',             ST_MakePoint(-73.7781, 40.6413)::geography),
 ('GCM','Ilhas Cayman','Ilhas Cayman', ST_MakePoint(-81.3577, 19.2928)::geography),
 ('LIS','Lisboa','Portugal',           ST_MakePoint( -9.1342, 38.7742)::geography),
 ('MAD','Madri','Espanha',             ST_MakePoint( -3.5676, 40.4983)::geography),
 ('CDG','Paris','França',              ST_MakePoint(  2.5479, 49.0097)::geography),
 ('DXB','Dubai','Emirados Árabes',     ST_MakePoint( 55.3657, 25.2532)::geography);

-- Cada linha é um voo de ida; a volta é cadastrada logo abaixo
INSERT INTO rota (origem, destino) VALUES
 ('GRU','GIG'),('GRU','BSB'),('GRU','CNF'),('GRU','SSA'),('GRU','REC'),('GRU','FOR'),
 ('GRU','POA'),('GRU','CWB'),('GRU','FLN'),('GRU','MAO'),('GRU','IGU'),('GRU','EZE'),
 ('GRU','SCL'),('GRU','LIS'),('GRU','MIA'),('GRU','JFK'),('GRU','MAD'),('GRU','CDG'),
 ('GRU','DXB'),
 ('GIG','BSB'),('GIG','CNF'),('GIG','SSA'),('GIG','VIX'),('GIG','LIS'),('GIG','MIA'),('GIG','EZE'),
 ('BSB','CNF'),('BSB','GYN'),('BSB','CGB'),('BSB','MAO'),('BSB','BEL'),('BSB','SLZ'),
 ('BSB','THE'),('BSB','SSA'),('BSB','FOR'),('BSB','REC'),('BSB','PVH'),
 ('CNF','VIX'),('CNF','SSA'),
 ('SSA','REC'),('SSA','MCZ'),('SSA','LIS'),
 ('REC','NAT'),('REC','FOR'),('REC','FEN'),('REC','MCZ'),('REC','LIS'),
 ('FOR','NAT'),('FOR','SLZ'),('FOR','THE'),('FOR','LIS'),
 ('POA','CWB'),('POA','FLN'),('POA','EZE'),
 ('CWB','FLN'),('CWB','IGU'),('CWB','CGR'),
 ('CGR','CGB'),('CGR','IGU'),
 ('CGB','PVH'),
 ('MAO','PVH'),('MAO','BEL'),('MAO','MIA'),
 ('BEL','SLZ'),
 ('MIA','JFK'),('MIA','GCM'),
 ('JFK','CDG'),
 ('LIS','MAD'),('LIS','CDG'),
 ('MAD','CDG'),
 ('CDG','DXB'),
 ('SCL','EZE');

-- volta de todas as rotas (grafo não-direcionado na prática)
INSERT INTO rota (origem, destino) SELECT destino, origem FROM rota;

-- O CUSTO de cada aresta: distância real calculada pelo PostGIS (em km).
-- ST_Distance em GEOGRAPHY mede em metros sobre o elipsoide da Terra.
CREATE VIEW rota_com_distancia AS
SELECT r.origem,
       r.destino,
       ROUND((ST_Distance(o.geom, d.geom) / 1000)::numeric, 1) AS distancia_km
FROM rota r
JOIN aeroporto o ON o.iata = r.origem
JOIN aeroporto d ON d.iata = r.destino;
