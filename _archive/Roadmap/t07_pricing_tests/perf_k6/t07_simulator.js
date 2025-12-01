// k6 load test: Simulator p95 under 200ms
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 20,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(95)<200'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AUTH = __ENV.AUTH_TOKEN || 'devtoken';

export default function () {
  const payload = JSON.stringify({
    client_id: 'client_fr_pro',
    cuvee_id: 'X',
    uom_id: 'bottle_75',
    quantity: 12,
    date: '2025-10-10',
    currency: 'EUR',
    explain: false
  });
  const res = http.post(`${BASE_URL}/tarifs/simulateur`, payload, {
    headers: { 'Authorization': `Bearer ${AUTH}`, 'Content-Type': 'application/json' },
    timeout: '30s'
  });
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has total_ttc': (r) => r.json('total_ttc') !== undefined,
  });
  sleep(0.2);
}
