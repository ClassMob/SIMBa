import os
import json
import math
import pandas as pd

# ==========================================
# 1. OUTILS MATHÉMATIQUES
# ==========================================
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def time_string_to_seconds(t):
    if pd.isna(t): return 0
    h, m, s = map(int, str(t).split(':'))
    return h * 3600 + m * 60 + s

# ==========================================
# 2. GÉNÉRATION DES NOEUDS (JSON)
# ==========================================
def create_nodes(path_arrets, path_velov):
    print("📍 1. Extraction des Noeuds...")
    nodes = {}

    with open(path_arrets, 'r', encoding='utf-8') as f:
        tcl_data = json.load(f)
        for item in tcl_data.get('values', []):
            if item.get('lat') and item.get('lon'):
                node_id = f"TCL_{item['id']}"
                nodes[node_id] = {
                    "id": node_id, "nom": item['nom'],
                    "lat": float(item['lat']), "lon": float(item['lon']), "type": "TCL"
                }

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
# 3. GÉNÉRATION DES MOBILITÉS ACTIVES (MARCHE & VÉLO)
# ==========================================
def create_active_mobility_edges(nodes_dict):
    print("🚶🚲 2. Calcul du maillage actif (Marche < 1.5km, Vélo < 3km)...")
    edges = []
    nodes_list = list(nodes_dict.values())
    
    for i in range(len(nodes_list)):
        for j in range(i + 1, len(nodes_list)):
            n1, n2 = nodes_list[i], nodes_list[j]
            dist = haversine_distance(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
            
            # --- RÈGLE 1 : LE RÉSEAU VÉLO ---
            # Si ce sont deux stations Vélo'v proches, on les relie en vélo
            if n1['type'] == 'VELOV' and n2['type'] == 'VELOV':
                if dist <= 3000: # 3 km max
                    time_sec = int(dist / 4.16) # Vitesse vélo ~15 km/h
                    edges.append({"source": n1['id'], "target": n2['id'], "mode": "VELO", "weight_time": time_sec, "weight_co2": 0})
                    edges.append({"source": n2['id'], "target": n1['id'], "mode": "VELO", "weight_time": time_sec, "weight_co2": 0})
            
            # --- RÈGLE 2 : LE RÉSEAU PIÉTON (CORRESPONDANCES) ---
            # On autorise la marche partout (TCL-TCL, VELOV-VELOV, TCL-VELOV) si c'est assez proche
            if dist <= 1500: # 1.5 km max à pied
                time_sec = int(dist / 1.4) # Vitesse piéton ~5 km/h
                edges.append({"source": n1['id'], "target": n2['id'], "mode": "MARCHE", "weight_time": time_sec, "weight_co2": 0})
                edges.append({"source": n2['id'], "target": n1['id'], "mode": "MARCHE", "weight_time": time_sec, "weight_co2": 0})
    
    print(f"   -> {len(edges)} arêtes actives créées.")
    return edges

# ==========================================
# 4. GÉNÉRATION DES ARÊTES GTFS (MÉTRO/BUS)
# ==========================================
def create_transit_edges(path_raw, nodes_dict):
    print("🚇 3. Traitement des fichiers GTFS avec Pandas...")
    
    try:
        routes = pd.read_csv(os.path.join(path_raw, 'routes.txt'), usecols=['route_id', 'route_short_name'])
        trips = pd.read_csv(os.path.join(path_raw, 'trips.txt'), usecols=['route_id', 'trip_id'])
        stop_times = pd.read_csv(os.path.join(path_raw, 'stop_times.txt'), usecols=['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'])

        df = pd.merge(stop_times, trips, on='trip_id')
        df = pd.merge(df, routes, on='route_id')
        df = df.sort_values(['trip_id', 'stop_sequence'])

        df['next_stop_id'] = df['stop_id'].shift(-1)
        df['next_arrival_time'] = df['arrival_time'].shift(-1)
        df['next_trip_id'] = df['trip_id'].shift(-1)

        edges_df = df[df['trip_id'] == df['next_trip_id']].copy()
        edges_df['time_sec'] = edges_df['next_arrival_time'].apply(time_string_to_seconds) - edges_df['departure_time'].apply(time_string_to_seconds)
        edges_df = edges_df[(edges_df['time_sec'] > 0) & (edges_df['time_sec'] < 3600)]

        unique_edges = edges_df.groupby(['stop_id', 'next_stop_id', 'route_short_name']).agg({'time_sec': 'mean'}).reset_index()

        transit_edges = []
        for _, row in unique_edges.iterrows():
            source = f"TCL_{int(row['stop_id'])}"
            target = f"TCL_{int(row['next_stop_id'])}"
            
            if source in nodes_dict and target in nodes_dict:
                transit_edges.append({
                    "source": source,
                    "target": target,
                    "mode": f"LIGNE_{row['route_short_name']}",
                    "weight_time": int(row['time_sec']),
                    "weight_co2": int((row['time_sec'] * 8.3) * 0.004) # Estimation CO2 (g)
                })
                
        print(f"   -> {len(transit_edges)} arêtes de transport créées.")
        return transit_edges
    except Exception as e:
        print(f"⚠️ Erreur lors du traitement GTFS (fichiers absents ou mal formatés). On ignore les transports.")
        return []

# ==========================================
# SCRIPT PRINCIPAL
# ==========================================
if __name__ == "__main__":
    RAW_DIR = '../data/raw'
    PROC_DIR = '../data/processed'
    os.makedirs(PROC_DIR, exist_ok=True)
    
    nodes_dict = create_nodes(
        os.path.join(RAW_DIR, 'tcl_arrets.json'),
        os.path.join(RAW_DIR, 'velov_stations.json')
    )
    
    edges_active = create_active_mobility_edges(nodes_dict)
    edges_transit = create_transit_edges(RAW_DIR, nodes_dict)
    
    simba_graph = {
        "nodes": list(nodes_dict.values()),
        "edges": edges_active + edges_transit
    }
    
    output_path = os.path.join(PROC_DIR, 'simba_graph.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(simba_graph, f, ensure_ascii=False, indent=2)
        
    print(f"✅ SUCCÈS : Graphe intermodal prêt pour JAVA exporté dans {output_path}")