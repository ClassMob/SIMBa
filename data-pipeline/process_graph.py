import os
import json
import math
import pandas as pd

# ==========================================
# 1. OUTILS MATHÉMATIQUES
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def time_string_to_seconds(t):
    """Convertit l'heure GTFS (ex: '08:30:00' ou '25:15:00') en secondes."""
    if pd.isna(t): return 0
    h, m, s = map(int, str(t).split(':'))
    return h * 3600 + m * 60 + s

# ==========================================
# 2. GÉNÉRATION DES NOEUDS (JSON)
def create_nodes(path_arrets, path_velov):
    print("1. Extraction des Noeuds...")
    nodes = {} # Dictionnaire pour un accès ultra-rapide (O(1)) 

    # Nœuds TCL
    with open(path_arrets, 'r', encoding='utf-8') as f:
        tcl_data = json.load(f)
        for item in tcl_data.get('values', []):
            if item.get('lat') and item.get('lon'):
                node_id = f"TCL_{item['id']}"
                nodes[node_id] = {
                    "id": node_id, "nom": item['nom'],
                    "lat": float(item['lat']), "lon": float(item['lon']), "type": "TCL"
                }

    # Nœuds Vélo'v
    with open(path_velov, 'r', encoding='utf-8') as f:
        velov_data = json.load(f)
        for item in velov_data.get('values', []):
            if item.get('lat') and item.get('lon'):
                node_id = f"VELOV_{item['idstation']}"
                nodes[node_id] = {
                    "id": node_id, "nom": item['nom'],
                    "lat": float(item['lat']), "lon": float(item['lon']), "type": "VELOV"
                }
    
    print(f"   -> {len(nodes)} nœuds créés.")
    return nodes

# ==========================================
# 3. GÉNÉRATION DES ARÊTES DE MARCHE (INTERMODALITÉ)
def create_walk_edges(nodes_dict):
    print("2. Calcul des arêtes de marche (Correspondances < 300m)...")
    edges = []
    nodes_list = list(nodes_dict.values())
    
    for i in range(len(nodes_list)):
        for j in range(i + 1, len(nodes_list)):
            n1, n2 = nodes_list[i], nodes_list[j]
            dist = haversine_distance(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
            
            if dist <= 300: # 300 mètres max
                time_sec = int(dist / 1.4) # Vitesse piéton ~5 km/h
                # Lien Bidirectionnel
                edges.append({"source": n1['id'], "target": n2['id'], "mode": "MARCHE", "weight_time": time_sec, "weight_co2": 0})
                edges.append({"source": n2['id'], "target": n1['id'], "mode": "MARCHE", "weight_time": time_sec, "weight_co2": 0})
    
    print(f"   -> {len(edges)} arêtes piétonnes créées.")
    return edges

# ==========================================
# 4. GÉNÉRATION DES ARÊTES GTFS (LE COEUR DU RÉSEAU)
def create_transit_edges(path_raw, nodes_dict):
    print("3. Traitement des fichiers GTFS avec Pandas...")
    
    # Chargement des fichiers GTFS (Attention à la RAM, on lit juste ce qu'il faut)
    routes = pd.read_csv(os.path.join(path_raw, 'routes.txt'), usecols=['route_id', 'route_short_name'])
    trips = pd.read_csv(os.path.join(path_raw, 'trips.txt'), usecols=['route_id', 'trip_id'])
    stop_times = pd.read_csv(os.path.join(path_raw, 'stop_times.txt'), usecols=['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'])

    # Jointures pour associer chaque arrêt à sa ligne (Route)
    df = pd.merge(stop_times, trips, on='trip_id')
    df = pd.merge(df, routes, on='route_id')

    # Tri par Trajet puis par ordre chronologique des arrêts
    df = df.sort_values(['trip_id', 'stop_sequence'])

    # MAGIE PANDAS : On décale les colonnes vers le haut pour avoir la ligne A -> B sur une seule ligne
    df['next_stop_id'] = df['stop_id'].shift(-1)
    df['next_arrival_time'] = df['arrival_time'].shift(-1)
    df['next_trip_id'] = df['trip_id'].shift(-1)

    # On ne garde que les lignes où l'arrêt suivant appartient au même trajet
    edges_df = df[df['trip_id'] == df['next_trip_id']].copy()

    # Calcul du temps de trajet en secondes
    edges_df['time_sec'] = edges_df['next_arrival_time'].apply(time_string_to_seconds) - edges_df['departure_time'].apply(time_string_to_seconds)
    
    # On gère les erreurs de données (temps négatifs ou aberrants)
    edges_df = edges_df[(edges_df['time_sec'] > 0) & (edges_df['time_sec'] < 3600)]

    # AGRÉGATION : On fait la moyenne du temps pour chaque segment (A -> B)
    unique_edges = edges_df.groupby(['stop_id', 'next_stop_id', 'route_short_name']).agg({'time_sec': 'mean'}).reset_index()

    transit_edges = []
    for _, row in unique_edges.iterrows():
        source = f"TCL_{int(row['stop_id'])}"
        target = f"TCL_{int(row['next_stop_id'])}"
        
        # On vérifie que les noeuds existent bien dans notre JSON
        if source in nodes_dict and target in nodes_dict:
            transit_edges.append({
                "source": source,
                "target": target,
                "mode": f"LIGNE_{row['route_short_name']}",
                "weight_time": int(row['time_sec']),
                "weight_co2": int((row['time_sec'] * 8.3) * 0.004) # Estimation CO2
            })
            
    print(f"   -> {len(transit_edges)} arêtes de transport créées.")
    return transit_edges

# ==========================================
# SCRIPT PRINCIPAL
if __name__ == "__main__":
    RAW_DIR = '../data/raw'
    PROC_DIR = '../data/processed'
    os.makedirs(PROC_DIR, exist_ok=True)
    
    # 1. Noeuds
    nodes_dict = create_nodes(
        os.path.join(RAW_DIR, 'tcl_arrets.json'),
        os.path.join(RAW_DIR, 'velov_stations.json')
    )
    
    # 2. Arêtes (Marche + GTFS)
    edges_walk = create_walk_edges(nodes_dict)
    edges_transit = create_transit_edges(RAW_DIR, nodes_dict)
    
    # 3. Assemblage du JSON Final
    simba_graph = {
        "nodes": list(nodes_dict.values()),
        "edges": edges_walk + edges_transit
    }
    
    # 4. Sauvegarde
    output_path = os.path.join(PROC_DIR, 'simba_graph.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(simba_graph, f, ensure_ascii=False, indent=2)
        
    print(f"SUCCÈS : Graphe prêt pour JAVA exporté dans {output_path}")