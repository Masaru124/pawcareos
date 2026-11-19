import { describe, expect, it } from 'vitest';

import { apiDetail } from '../src/lib/session';

describe('apiDetail', () => {
  it('returns a plain FastAPI detail', () => {
    expect(apiDetail({ detail: 'Patient not found' }, 'fallback')).toBe('Patient not found');
  });

  it('flattens a validation error with its field path', () => {
    const body = {
      detail: [
        {
          loc: ['body', 'medications', 0, 'name'],
          msg: 'Value error, Add at least one medication or vaccine',
          type: 'value_error',
        },
      ],
    };
    expect(apiDetail(body, 'fallback')).toBe(
      'medications.0.name: Add at least one medication or vaccine',
    );
  });

  it('strips the pydantic prefix when there is no path', () => {
    expect(apiDetail({ detail: [{ loc: ['body'], msg: 'Value error, Required' }] }, 'x')).toBe(
      'Required',
    );
  });

  it('falls back on shapes it does not recognise', () => {
    expect(apiDetail(null, 'fallback')).toBe('fallback');
    expect(apiDetail('not json', 'fallback')).toBe('fallback');
    expect(apiDetail({}, 'fallback')).toBe('fallback');
    expect(apiDetail({ detail: [] }, 'fallback')).toBe('fallback');
    expect(apiDetail({ detail: { nested: true } }, 'fallback')).toBe('fallback');
    expect(apiDetail({ detail: [{ type: 'missing' }] }, 'fallback')).toBe('fallback');
  });
});
