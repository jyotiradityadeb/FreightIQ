import test from 'node:test';
import assert from 'node:assert/strict';
import handler from '../netlify/functions/api.mjs';

test('rejects unknown API paths before contacting Python', async () => {
  const response = await handler(new Request('http://localhost/api/unknown'));
  assert.equal(response.status, 404);
});

test('enforces read and write methods for new Stitch endpoints', async () => {
  const read = await handler(new Request('http://localhost/api/stitch/explorer', { method: 'POST' }));
  const write = await handler(new Request('http://localhost/api/stitch/solve'));
  assert.equal(read.status, 405);
  assert.equal(write.status, 405);
  assert.equal((await handler(new Request('http://localhost/api/web/strategy-arena'))).status, 405);
  assert.equal((await handler(new Request('http://localhost/api/web/arena-report'))).status, 405);
});

test('reports an unconfigured Python service clearly', async () => {
  const prior = process.env.FREIGHTIQ_API_URL;
  delete process.env.FREIGHTIQ_API_URL;
  try {
    const response = await handler(new Request('http://localhost/api/stitch/integrations'));
    assert.equal(response.status, 503);
    assert.match((await response.json()).detail, /FREIGHTIQ_API_URL/);
  } finally {
    if (prior === undefined) delete process.env.FREIGHTIQ_API_URL;
    else process.env.FREIGHTIQ_API_URL = prior;
  }
});
