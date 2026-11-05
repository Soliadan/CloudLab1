# Load Testing

## 1. Tool

k6 v2.3.0

## 2. Test Scenario

The test simulates users performing one write operation followed by nine read operations.

Each iteration includes:

- 1 POST /orders — create an order.
- 3 GET /orders — retrieve the list of orders.
- 6 GET /orders/{id} — retrieve the newly created order.

The workload follows a 1:9 write-to-read ratio.

## 3. Load Configuration

- Virtual users: 20
- Ramp-up: 3 minutes (0 to 20 users)
- Steady load: 5 minutes (20 users)
- Ramp-down: 2 minutes (20 to 0 users)
- Total configured duration: 10 minutes

## 4. Run Command

`k6 run --env USERS=20 --summary-export=loadtest/results-dashboard.json loadtest/test.js`

The test was executed against the AWS-hosted Flask API through the Application Load Balancer.

## 5. Test Results

Results from `loadtest/results-dashboard.json`:

| Metric | Result |
|---|---|
| Total HTTP requests | 17,630 |
| Request rate | 29.31 req/s |
| Failed HTTP requests | 0 |
| HTTP error rate | 0% |
| p50 latency | 402.83 ms |
| p95 latency | 809.55 ms |
| p99 latency | 1067.37 ms |
| Successful checks | 100% |
| Completed iterations | 1,763 |
| Maximum virtual users | 20 |

All HTTP requests in this test completed successfully.

The p95 latency of 809.55 ms means that 95% of requests completed within approximately 810 milliseconds.

## 6. Autoscaling Results

The ECS service initially had 1 running task.

During the load test, CPU utilization exceeded the configured target of 60% and reached approximately 99%.

AWS Application Auto Scaling automatically increased the number of ECS tasks:

- From 1 to 2 tasks.
- From 2 to 3 tasks.

After the load test, CPU utilization decreased to approximately 2.7%.

AWS gradually reduced the number of tasks:

- From 3 to 2 tasks.
- From 2 to 1 task.

The final ECS service state was:

- Desired tasks: 1
- Running tasks: 1
- Pending tasks: 0

Both scale-out and scale-in were successfully verified.

## 7. Conclusion

The load test successfully demonstrated horizontal autoscaling of the AWS ECS service.

The application processed 17,630 HTTP requests without HTTP request failures during the selected test.

CPU utilization increased under load, triggering automatic scaling from 1 to 3 tasks.

After the workload decreased, AWS automatically returned the service to 1 running task.

The results confirm that the configured autoscaling policy responds to increasing and decreasing workloads.