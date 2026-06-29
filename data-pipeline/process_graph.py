import os
import json
from typing import Tuple, Dict

def load_raw_data() -> Tuple[Dict, Dict, Dict]:
    tcl_arrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", "tcl_arrets.json")
    
    tcl_lignes_metro_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", "tcl_lignes_metro.json")
    
    velov_stations_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", "velov_stations.json")
    
    with open(tcl_arrets_path, 'r', encoding="utf-8") as f:
        tcl_data = json.load(f)
        
    
    with open(tcl_lignes_metro_path, 'r', encoding="utf-8") as f:
        tcl_lignes_metro = json.load(f)
        
    
    with open(velov_stations_path, 'r', encoding="utf-8") as f:
        velov_stations = json.load(f)
        
    
        
    return tcl_data, tcl_lignes_metro, velov_stations


tcl_data, tcl_lignes_metro, velov_stations = load_raw_data()

print(tcl_data)
print()
print(tcl_lignes_metro)
print()
print(velov_stations)