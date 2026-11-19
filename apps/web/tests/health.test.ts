import { describe, expect, it } from 'vitest';

import { GET } from '../src/app/api/health/route';

describe('web health route', () => {
  it('answers ok so the web runtime has its own liveness check', async () => {
    const res = await GET();
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ status: 'ok' });
  });
});
