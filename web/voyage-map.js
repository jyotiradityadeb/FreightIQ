import * as maplibregl from './maplibre-gl.mjs';

maplibregl.setWorkerUrl('/maplibre-gl-worker.mjs');

let activeMap = null;
let generation = 0;
let voyagesPromise;

function voyages() {
  voyagesPromise ||= fetch('/geo/voyages.json')
    .then(response => {
      if (!response.ok) throw new Error('Voyage geometry unavailable');
      return response.json();
    })
    .catch(error => { voyagesPromise = null; throw error; });
  return voyagesPromise;
}

function number(value, digits = 0) {
  return Number(value).toLocaleString('en-IN', {maximumFractionDigits: digits, minimumFractionDigits: digits});
}

function popup(title, lines) {
  const root = document.createElement('div');
  root.className = 'voyage-popup';
  const heading = document.createElement('strong');
  heading.textContent = title;
  root.append(heading);
  for (const line of lines) {
    const row = document.createElement('span');
    row.textContent = line;
    root.append(row);
  }
  return root;
}

function marker(map, point, kind, lines) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = `voyage-marker ${kind}`;
  button.setAttribute('aria-label', `${point.name}, ${point.country}. Open port details`);
  button.title = `${point.name} · ${point.country}`;
  const dot = document.createElement('span');
  dot.className = 'voyage-marker-dot';
  const label = document.createElement('span');
  label.className = 'voyage-marker-label';
  label.textContent = point.name.toUpperCase();
  button.append(dot, label);
  const tip = new maplibregl.Popup({offset: 18, closeButton: false, closeOnClick: false, maxWidth: '240px'})
    .setDOMContent(popup(point.name, [`${point.country} · ${kind === 'origin' ? 'Shipment origin' : 'Destination port'}`, ...lines, point.source || 'Coordinate source unavailable']));
  const pin = new maplibregl.Marker({element: button, anchor: 'bottom'}).setLngLat(point.coordinates).addTo(map);
  button.addEventListener('click', event => { event.stopPropagation(); tip.isOpen() ? tip.remove() : tip.setLngLat(point.coordinates).addTo(map); });
  return pin;
}

function fit(map, points, animated = true) {
  const bounds = points.reduce((box, point) => box.extend(point), new maplibregl.LngLatBounds(points[0], points[0]));
  map.fitBounds(bounds, {padding: {top: 58, bottom: 54, left: 68, right: 68}, maxZoom: 5.5, duration: animated ? 400 : 0});
}

function signals(container, context) {
  const target = container.querySelector('[data-voyage-signals]');
  const items = [];
  if (Number.isFinite(Number(context.congestion))) items.push(`DESTINATION CONGESTION · ${number(context.congestion, 1)} / 100 synthetic`);
  if (Number.isFinite(Number(context.waitingHours))) items.push(`PORT WAIT · ${number(context.waitingHours, 1)} h synthetic`);
  if (Number.isFinite(Number(context.weather))) items.push(`WEATHER RISK · ${number(context.weather, 1)} synthetic score`);
  const shock = context.scenario;
  if (shock && Object.keys(shock).length) {
    const parts = [];
    if (Number(shock.port_congestion_shock_pct)) parts.push(`${number(shock.port_congestion_shock_pct)}% congestion shock`);
    if (shock.weather_risk_level && shock.weather_risk_level !== 'Low') parts.push(`${shock.weather_risk_level} weather setting`);
    if (parts.length) items.push(`SCENARIO INPUT · ${parts.join(' · ')}`);
    if (shock.costBaseline && shock.costStressed) items.push(`SCENARIO MODEL COST · ${shock.costBaseline} → ${shock.costStressed}`);
  }
  if (!items.length) items.push('Operational indicators unavailable for this route.');
  for (const item of items) {
    const chip = document.createElement('span');
    chip.textContent = item;
    target.append(chip);
  }
}

export function disposeVoyageMap() {
  generation++;
  if (activeMap) activeMap.remove();
  activeMap = null;
}

export async function mountVoyageMap(container) {
  disposeVoyageMap();
  const ticket = generation;
  let context;
  try { context = JSON.parse(container.dataset.context); }
  catch { container.querySelector('.voyage-map-surface').textContent = 'Shipment details unavailable.'; return; }
  signals(container, context);
  const surface = container.querySelector('.voyage-map-surface');
  const selected = container.querySelector('[data-voyage-view="selected"]');
  const alternatives = container.querySelector('[data-voyage-view="alternatives"]');
  const alternativePanel = container.querySelector('.voyage-alternatives');
  const mapWrap = container.querySelector('.voyage-map-wrap');
  for (const button of [selected, alternatives]) button.addEventListener('click', () => {
    const showMap = button === selected;
    selected.classList.toggle('active', showMap);
    alternatives.classList.toggle('active', !showMap);
    selected.setAttribute('aria-selected', String(showMap));
    alternatives.setAttribute('aria-selected', String(!showMap));
    mapWrap.hidden = !showMap;
    alternativePanel.hidden = showMap;
    if (showMap) activeMap?.resize();
  });

  let voyage;
  try { voyage = (await voyages()).routes[context.routeKey]; }
  catch { surface.textContent = 'Map data unavailable. Select a route again to retry.'; return; }
  if (ticket !== generation || !container.isConnected) return;
  if (!voyage?.origin?.coordinates || !voyage?.destination?.coordinates || !voyage?.coordinates?.length) {
    surface.textContent = 'No geographic corridor is available for this shipment.';
    return;
  }
  const distance = Number(voyage.distance_nm);
  const speed = Number(context.speed);
  if (Number.isFinite(distance) && distance > 0) {
    container.querySelector('[data-voyage-distance]').textContent = `≈ ${number(distance)} NM`;
    if (Number.isFinite(speed) && speed > 0) {
      container.querySelector('[data-voyage-transit]').textContent = `≈ ${number(distance / speed / 24, 1)} DAYS`;
      container.querySelector('[data-voyage-transit]').nextElementSibling.textContent = `At ${number(speed, 1)} kn · sea time only`;
    }
  }
  const corridor = {type: 'Feature', properties: {}, geometry: {type: 'LineString', coordinates: voyage.coordinates}};
  try {
    surface.textContent = '';
    const map = new maplibregl.Map({
      container: surface,
      style: {
        version: 8,
        sources: {
          land: {type: 'geojson', data: '/geo/land.geojson', attribution: 'Natural Earth (public domain)'},
          corridor: {type: 'geojson', data: corridor},
        },
        layers: [
          {id: 'ocean', type: 'background', paint: {'background-color': '#071d2c'}},
          {id: 'land', type: 'fill', source: 'land', paint: {'fill-color': '#16384a', 'fill-opacity': 0.96}},
          {id: 'coast', type: 'line', source: 'land', paint: {'line-color': '#54778a', 'line-width': 0.7, 'line-opacity': 0.65}},
          {id: 'corridor-glow', type: 'line', source: 'corridor', paint: {'line-color': '#35d6e8', 'line-width': 9, 'line-opacity': 0.18, 'line-blur': 5}},
          {id: 'corridor', type: 'line', source: 'corridor', paint: {'line-color': '#41deb9', 'line-width': 2.5, 'line-opacity': 0.95}},
        ],
      },
      center: voyage.origin.coordinates,
      zoom: 2,
      minZoom: 1,
      maxZoom: 8,
      attributionControl: false,
    });
    activeMap = map;
    marker(map, voyage.origin, 'origin', [`${number(context.quantity)} t ${context.cargo}`, 'Demo shipment · no live departure feed']);
    marker(map, voyage.destination, 'destination', [
      Number.isFinite(Number(context.congestion)) ? `Synthetic congestion ${number(context.congestion, 1)} / 100` : 'Congestion unavailable',
      'No live arrival estimate',
    ]);
    const points = [...voyage.coordinates, voyage.origin.coordinates, voyage.destination.coordinates];
    map.once('load', () => fit(map, points, false));
    container.querySelector('.voyage-reset').addEventListener('click', () => fit(map, points));
    map.on('click', 'corridor', event => new maplibregl.Popup({closeButton: false})
      .setLngLat(event.lngLat)
      .setDOMContent(popup('Illustrative sea corridor', ['Open-source shortest-sea graph', 'Routing and navigability not verified']))
      .addTo(map));
    map.on('mouseenter', 'corridor', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'corridor', () => { map.getCanvas().style.cursor = ''; });
    map.on('error', event => {
      console.error('Voyage map:', event.error);
      if (event.error?.message?.includes('land.geojson')) {
        container.querySelector('.voyage-map-note').textContent = 'BASEMAP UNAVAILABLE · ILLUSTRATIVE CORRIDOR ONLY';
      }
    });
  } catch (error) {
    console.error(error);
    disposeVoyageMap();
    surface.textContent = 'Interactive map unavailable. Voyage metrics remain available.';
  }
}
