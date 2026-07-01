import { useState } from 'react';
import type { RouteResponse } from './types/RouteTypes';
import { fetchShortestPath } from './services/apiService';
import RouteDetails from './components/RouteDetails';
import MapDisplay from './components/MapDisplay';

function App() {
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculateRoute = async () => {
    setLoading(true);
    setError(null);
    try {
      // Pour l'instant on garde les ID en dur, on pourra créer un formulaire plus tard
      const data = await fetchShortestPath('TCL_10435', 'TCL_10437', 'time');
      setRoute(data);
    } catch (err) {
      if (err instanceof Error){
        setError(err.message);
      }
      else{
        setError("Une erreur inattendue s'est produite");
      }
      
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '900px', margin: '0 auto' }}>
      <h1>🦁SIMBa - Routage Écologique</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={handleCalculateRoute} 
          disabled={loading} 
          style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
        >
          {loading ? 'Calcul en cours...' : 'Calculer le trajet de test'}
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>❌ {error}</p>}

      {route && <RouteDetails route={route} />}
      
      {/* On affiche la carte en lui passant le chemin (vide par défaut) */}
      <MapDisplay path={route?.path || []} />
    </div>
  );
}

export default App;