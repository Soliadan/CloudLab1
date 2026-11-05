
# Load Testing

## 1. Tool

k6 v2.3.0

## 2. Test Scenario

The test simulates users performing one write operation and nine read operations.

- POST /orders — create an order
- GET /orders — retrieve orders
- GET /orders/{id} — retrieve an order

## 3. Load Configuration

- Virtual users: 20
- Ramp-up: 3 minutes (0 to 20 users)
- Steady load: 5 minutes (20 users)
- Ramp-down: 2 minutes (20 to 0 users)

## 4. Run Command

```bash
k6 run --env USERS=20 --summary-export=loadtest/results.json loadtest/test.js
```

## 5. Test Results

| Metric | Result |
|---|---|
| Total HTTP requests | 18,345 |
| Request rate | 24.57 req/s |
| Failed requests | 30 |
| Error rate | 0.16% |
| p50 latency | 200.56 ms |
| p95 latency | 778.86 ms |
| p99 latency | 3.02 s |
| Successful checks | 99.83% |
| Maximum virtual users | 20 |

## 6. Autoscaling Results

The ECS service initially had 1 running task.

During the load test, CPU utilization exceeded the target value of 60%.

AWS Application Auto Scaling increased the desired number of tasks from 1 to 2.

The scale-out operation completed successfully.

Scale-in to 1 task was not yet confirmed at the time of the initial verification.

## 7. Conclusion

The load test successfully triggered horizontal autoscaling.

The service handled 18,345 HTTP requests with a 0.16% error rate.

Some requests timed out during high load. The p95 response time was 778.86 ms.
