// k6 read test: Price list read p95 under 600ms
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(95)<600'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AUTH = __ENV.AUTH_TOKEN || 'devtoken';

export default function () {
  const res = http.get(`${BASE_URL}/tarifs/listes?segment=business&country=FR&currency=EUR`, {
    headers: { 'Authorization': `Bearer ${AUTH}` },
    timeout: '30s'
  });
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(0.5);
}
