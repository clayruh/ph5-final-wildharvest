import { useRef, useEffect, useState } from 'react';
import 'mapbox-gl/dist/mapbox-gl.css';
import mapboxgl from 'mapbox-gl';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_KEY;

export default function MapBox() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [pins, setPins] = useState([]);
  const [selectedPin, setSelectedPin] = useState(null);

  // Fetch pin data and initialize the map
  useEffect(() => {
    fetch('http://localhost:5555/api/v1/pins')
      .then((res) => res.json())
      .then((allData) => {
        setPins(allData);

        if (!map.current) {
          map.current = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/streets-v11',
            center: [-73.916369, 40.724461],
            zoom: 11,
          });
        }

        allData.forEach((pinObj) => {
          const marker = new mapboxgl.Marker()
            .setLngLat([pinObj.longitude, pinObj.latitude])
            .setPopup(
              new mapboxgl.Popup().setHTML(
                `
                <div className="mapbox-popup">
                  <div className="mapbox-popup-img">
                    <img src="${pinObj.image}" alt=${pinObj.plant.plant_name}/>
                  </div>
                  <div className="mapbox-popup-text">
                    <h3>${pinObj.plant.plant_name}</h3>
                    <p>${pinObj.comment}</p>
                    <p> - ${pinObj.user.username}</p>
                  </div>
                </div>
                `
              )
            )
            .addTo(map.current);

          // event listener to the marker
          marker.getElement().addEventListener('click', () => {
            setSelectedPin(pinObj);
          });
        });
      });
  }, []);

  // Zoom to the selected pin
  useEffect(() => {
    if (selectedPin) {
      map.current.flyTo({
        center: [selectedPin.longitude, selectedPin.latitude],
        zoom: 11,
        duration: 2500,
      });
    }
  }, [selectedPin]);

  const mapPins = pins.map((pinObj) => (
    <div key={pinObj.id}>
      <img src={pinObj.image} style={{ width: 50 + 'px' }} alt={pinObj.plant.plant_name}/>
      <h4>{pinObj.plant.plant_name}</h4>
      <p>{pinObj.longitude}</p>
      <p>{pinObj.latitude}</p>
      <p>{pinObj.user.username}</p>
    </div>
  ));

  return (
    <div>
      <div ref={mapContainer} className="map-container"></div>
      <div>{mapPins}</div>
    </div>
  );
}
