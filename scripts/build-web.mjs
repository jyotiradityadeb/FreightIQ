import { mkdir, copyFile } from 'node:fs/promises';
await mkdir('dist', { recursive: true });
// Explicit allowlist: Python sources, datasets and local secrets never enter the public bundle.
for (const name of ['index.html', 'app.js', 'styles.css']) {
  await copyFile(`web/${name}`, `dist/${name}`);
}
await copyFile('web/vendor/plotly.min.js', 'dist/plotly.min.js');
await copyFile('web/vendor/LICENSE.txt', 'dist/plotly-LICENSE.txt');
console.log('FreightIQ web client built in dist/');
