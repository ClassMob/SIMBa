import React from 'react';
import type { RouteResponse } from '../types/RouteTypes';

interface Props {
  route: RouteResponse;
}

const RouteDetails: React.FC<Props> = ({ route }) => {
  if (route.path.length === 0) return null;

  return (
    <div style={{ backgroundColor: '#e8f5e9', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
      <h3>✅ Trajet trouvé !</h3>
      <p>⏱️ Temps estimé : <strong>{route.totalTimeSeconds} secondes</strong></p>
      <p>🍃 Émissions CO2 : <strong>{route.totalCo2Grams} grammes</strong></p>
    </div>
  );
};

export default RouteDetails;