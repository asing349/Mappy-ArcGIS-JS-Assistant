import Map from "@arcgis/core/Map";
import MapView from "@arcgis/core/views/MapView";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import Graphic from "@arcgis/core/Graphic";
import Point from "@arcgis/core/geometry/Point";

// Create a new map
const map = new Map({
    basemap: "topo-vector"
});

// Create a 2D view
const view = new MapView({
    container: "viewDiv",
    map: map,
    center: [-118.805, 34.027],
    zoom: 13
});

// Add a feature layer
const layer = new FeatureLayer({
    url: "https://services.arcgis.com/..."
});

map.add(layer);

// Create a graphic
const point = new Point({
    longitude: -118.805,
    latitude: 34.027
});

const graphic = new Graphic({
    geometry: point
});