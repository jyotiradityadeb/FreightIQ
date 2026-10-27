const paths = new Set(['health', 'market/latest', 'web/catalog', 'web/data', 'web/forecast', 'web/optimize',
  'web/scenario', 'web/decision-twin', 'web/control-tower', 'web/backtest',
  'web/sensitivity', 'web/report', 'web/validation', 'data/upload',
  'stitch/explorer', 'stitch/explorer-summary', 'stitch/integrations', 'stitch/audit',
  'stitch/decisions', 'stitch/weather-chart', 'stitch/export/route', 'stitch/export/dataset',
  'stitch/solve', 'stitch/operator-note', 'stitch/upload']);
const error = (status, detail) => Response.json({ detail }, { status });

export default async function handler(request) {
  const incoming = new URL(request.url);
  const path = incoming.pathname.replace(/^\/(?:api\/|\.netlify\/functions\/api\/?)/, '');
  if (!paths.has(path)) return error(404, 'Unknown API endpoint');
  const readOnly = ['health', 'market/latest', 'web/catalog', 'web/data', 'web/validation',
    'stitch/explorer', 'stitch/explorer-summary', 'stitch/integrations', 'stitch/audit',
    'stitch/decisions', 'stitch/weather-chart', 'stitch/export/route', 'stitch/export/dataset'].includes(path);
  if (request.method !== (readOnly ? 'GET' : 'POST')) return error(405, 'Method not allowed');
  const base = process.env.FREIGHTIQ_API_URL;
  if (!base) return error(503, 'API not connected. Set FREIGHTIQ_API_URL in Netlify to your Python service URL, then redeploy.');
  try {
    const target = new URL(base);
    if (!['https:', 'http:'].includes(target.protocol)) return error(503, 'Invalid API service URL');
    target.pathname = `${target.pathname.replace(/\/$/, '')}/${path}`;
    target.search = incoming.search;
    const headers = { Accept: '*/*' };
    if (request.headers.get('content-type')) headers['Content-Type'] = request.headers.get('content-type');
    let body;
    if (!readOnly) {
      body = await request.arrayBuffer();
      if (body.byteLength > 2 * 1024 * 1024) return error(413, 'Maximum upload size is 2 MB');
    }
    const upstream = await fetch(target, { method: request.method, headers, body,
      redirect: 'error', signal: AbortSignal.timeout(55000) });
    return new Response(upstream.body, { status: upstream.status, headers: {
      'Content-Type': upstream.headers.get('content-type') || 'application/json',
      'Cache-Control': 'no-store',
      ...(upstream.headers.has('content-disposition') ? {
        'Content-Disposition': upstream.headers.get('content-disposition') } : {})
    }});
  } catch (err) {
    return error(err.name === 'TimeoutError' ? 504 : 502,
      'Python service unavailable or calculation timed out. Retry after the service starts, or use a shorter backtest period.');
  }
}
