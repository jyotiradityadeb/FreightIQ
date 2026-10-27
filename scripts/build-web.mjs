import { mkdir, copyFile } from 'node:fs/promises';
await mkdir('dist', { recursive: true });
// Explicit allowlist: Python sources, datasets and local secrets never enter the public bundle.
for (const name of ['index.html', 'app.js', 'styles.css']) {
  await copyFile(`web/${name}`, `dist/${name}`);
}
await copyFile('web/vendor/plotly.min.js', 'dist/plotly.min.js');
await copyFile('web/vendor/LICENSE.txt', 'dist/plotly-LICENSE.txt');
for (const name of ['maplibre-gl.mjs', 'maplibre-gl-worker.mjs', 'maplibre-gl.css', 'maplibre-LICENSE.txt']) {
  await copyFile(`web/vendor/${name}`, `dist/${name}`);
}
await copyFile('web/voyage-map.js', 'dist/voyage-map.js');
await mkdir('dist/geo', {recursive: true});
for (const name of ['land.geojson', 'voyages.json']) await copyFile(`web/geo/${name}`, `dist/geo/${name}`);
console.log('FreightIQ web client built in dist/');
