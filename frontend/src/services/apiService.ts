import type { RouteResponse } from '../types/RouteTypes';

const API_BASE_URL = 'http://localhost:8081/api';

export const fetchShortestPath = async (startId: string, endId: string, optimize: string = 'time'): Promise<RouteResponse> => {
  const response = await fetch(`${API_BASE_URL}/route?start=${startId}&end=${endId}&optimize=${optimize}`);
  
  if (!response.ok) {
    throw new Error("Erreur lors du calcul du trajet. Vérifiez que les arrêts existent.");
  }
  
  return await response.json();
};  