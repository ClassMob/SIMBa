export interface Node {
  id: string;
  nom: string;
  lat: number;
  lon: number;
  type: string;
}

export interface RouteResponse {
  path: Node[];
  totalTimeSeconds: number;
  totalCo2Grams: number;
}