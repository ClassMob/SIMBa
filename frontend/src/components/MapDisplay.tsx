import React from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet';
import type {Node} from '../types/RouteTypes';

interface Props {
  path: Node[];
}

const MapDisplay: React.FC<Props> = ({ path }) => {
  // Transformation des nœuds en coordonnées pour Leaflet
  const positions: [number, number][] = path.map(node => [node.lat, node.lon]);

  return (
    <MapContainer 
      center={[45.764, 4.835]} // Centre de Lyon
      zoom={13} 
      style={{ height: '500px', width: '100%', borderRadius: '8px', border: '2px solid #ccc' }}
    >
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {positions.length > 0 && (
        <Polyline positions={positions} color="red" weight={5} />
      )}

      {positions.length > 0 && (
        <>
          <Marker position={positions[0]}>
            <Popup>Départ : {path[0].nom}</Popup>
          </Marker>
          <Marker position={positions[positions.length - 1]}>
            <Popup>Arrivée : {path[path.length - 1].nom}</Popup>
          </Marker>
        </>
      )}
    </MapContainer>
  );
};

export default MapDisplay;