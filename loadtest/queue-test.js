
import http from 'k6/http';
import { check } from 'k6';

const BASE = 'http://cloudlab1-lab-1602657390.eu-north-1.elb.amazonaws.com';

export const options = {
    scenarios: {
        queue_test: {
            executor: 'constant-arrival-rate',
            rate: Number(__ENV.RATE || 1),
            timeUnit: '1s',
            duration: __ENV.DURATION || '2m',
            preAllocatedVUs: 10,
            maxVUs: 40
        }
    },
    summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)']
};

export default function () {
    const payload = JSON.stringify({
        parfume_name: 'SQS Load Test',
        Volume: '50ml',
        brand: 'Test',
        order_date: '2026-11-19',
        price: 100
    });

    const response = http.post(
        `${BASE}/async-orders`,
        payload,
        {
            headers: { 'Content-Type': 'application/json' },
            timeout: '10s'
        }
    );

    check(response, {
        'POST 202 Accepted': (r) => r.status === 202
    });
}
