
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://cloudlab1-lab-1602657390.eu-north-1.elb.amazonaws.com';
const N = Number(__ENV.USERS || 20);

export const options = {
  stages: [
    { duration: '3m', target: N },
    { duration: '5m', target: N },
    { duration: '2m', target: 0 },
  ],
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)'],
};

export default function () {
  const payload = JSON.stringify({
    parfume_name: 'LoadTest',
    Volume: '50ml',
    brand: 'Test',
    order_date: '2026-10-28',
    price: 100,
  });

  const post = http.post(`${BASE}/orders`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(post, { 'POST 201': (r) => r.status === 201 });

  if (post.status !== 201) return;

  const id = post.json('id');

  for (let i = 0; i < 9; i++) {
    const url = i % 3 === 0
      ? `${BASE}/orders`
      : `${BASE}/orders/${id}`;

    const res = http.get(url);
    check(res, { 'GET 200': (r) => r.status === 200 });
  }

  sleep(1);
}

