import os
import requests


def download_grandlyon_data(url: str, filename:str):
    print(f"⏳ Téléchargement de {filename}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        filepath = os.path.join("..","data", "raw", filename)
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(response.text)
            
        print(f"✅ Succès : {filename} sauvegardé dans {filepath}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du téléchargement de {filename}: {e}")
        
        
if __name__ == "__main__":
    
    # Création des dossiers data/raw/ s'ils n'existent pas déjà
    os.makedirs(os.path.join("..","data", "raw"), exist_ok=True)
    os.makedirs(os.path.join("..","data", "processed"), exist_ok=True)
    
    # 3. Dictionnaires des URLs (À remplacer par les URL d'export GeoJSON exactes du portail)
    # Exemple fictif basé sur la structure WFS de Grand Lyon :
    datasets = {
        "velov_stations.json": "https://data.grandlyon.com/fr/datapusher/ws/grandlyon/pvo_patrimoine_voirie.pvostationvelov/all.json?maxfeatures=10000&start=1&filename=stations-velo-v-metropole-lyon",
        "tcl_arrets.json": "https://data.grandlyon.com/fr/datapusher/ws/rdata/tcl_sytral.tclarret/all.json?maxfeatures=10000&start=1&filename=points-arret-reseau-transports-commun-lyonnais",
        "tcl_lignes_metro.json": "https://data.grandlyon.com/fr/datapusher/ws/rdata/tcl_sytral.tcllignemf_3/all.json?maxfeatures=10000&start=1&filename=lignes-metro-funiculaire-reseau-transports-commun-lyonnais-v2"
    }
    
    # 4. Lancement de la boucle de téléchargement
    for filename, url in datasets.items():
        download_grandlyon_data(url, filename)
        
    print("🚀 Pipeline d'extraction terminée !")
        
