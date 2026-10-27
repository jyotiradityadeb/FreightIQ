import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import handler from '../netlify/functions/api.mjs';
process.env.FREIGHTIQ_API_URL ||= 'http://127.0.0.1:8000';
const port = Number(process.env.WEB_PORT || 3000);
const files = { '/app.js': ['web/app.js', 'text/javascript'], '/styles.css': ['web/styles.css', 'text/css'],
  '/plotly.min.js': ['web/vendor/plotly.min.js', 'text/javascript'] };
createServer(async (req, res) => {
  try {
    if (req.url.startsWith('/api/')) {
      const chunks = [];
      let size = 0;
      for await (const chunk of req) {
        size += chunk.length;
        if (size > 2 * 1024 * 1024) { res.writeHead(413).end('Upload too large'); return; }
        chunks.push(chunk);
      }
      const response = await handler(new Request(`http://localhost:${port}${req.url}`, {
        method: req.method, headers: req.headers,
        ...(req.method === 'POST' ? { body: Buffer.concat(chunks) } : {})
      }));
      res.writeHead(response.status, Object.fromEntries(response.headers));
      res.end(Buffer.from(await response.arrayBuffer()));
    } else {
      const [file, type] = files[req.url.split('?')[0]] || ['web/index.html', 'text/html'];
      res.writeHead(200, { 'Content-Type': type });
      res.end(await readFile(file));
    }
  } catch { res.writeHead(500).end('Local server error'); }
}).listen(port, '127.0.0.1', () => console.log(`FreightIQ: http://localhost:${port}`));
