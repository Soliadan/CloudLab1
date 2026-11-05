
# Automatic Scaling

## Configuration

- Provider: AWS ECS Fargate
- Scaling: Horizontal, CPU-based
- Minimum tasks: 1
- Maximum tasks: 3
- Target CPU: 60%
- Scale-out cooldown: 60 seconds
- Scale-in cooldown: 300 seconds

## Justification

The CPU target of 60% leaves spare capacity
for increasing workloads.

The maximum of 3 tasks limits AWS costs.

## Cooldown

Cooldown prevents frequent scaling changes.

Without cooldown, the service could scale
too frequently, causing instability and
unnecessary resource usage.

## Test Results

During the k6 load test with 20 users,
CPU utilization exceeded 60%.

AWS successfully increased the number
of running tasks from 1 to 2.

Scale-in: pending verification.


## Monitoring

The CloudWatch Dashboard contains five graphs:
- Desired and running ECS tasks
- CPU utilization
- Requests per minute
- Response time p95
- HTTP 5xx errors

### Autoscaling and CPU Utilization

![Autoscaling and CPU](screenshots/autoscaling.png)

### Requests and Response Time

![Requests and Response Time](screenshots/metrics.png)



## Scaling Analysis

During the load test, CPU utilization increased above
the 60% threshold and reached approximately 99%.

AWS automatically increased the number of ECS tasks
from 1 to 2 and then to 3.

After the load test, CPU utilization decreased to
approximately 2.7%, and AWS gradually reduced
the number of tasks from 3 to 1.

Scaling does not happen immediately because AWS
needs time to collect and evaluate CloudWatch metrics.

The configured cooldown periods are:
- Scale-out: 60 seconds
- Scale-in: 300 seconds

These delays prevent frequent scaling changes
and help maintain service stability.

## Scaling Analysis

During the load test, CPU utilization increased above
the 60% threshold and reached approximately 99%.

AWS automatically increased the number of ECS tasks
from 1 to 2 and then to 3.

After the load test, CPU utilization decreased to
approximately 2.7%, and AWS gradually reduced
the number of tasks from 3 to 1.

Scaling does not happen immediately because AWS
needs time to collect and evaluate CloudWatch metrics.

The configured cooldown periods are:
- Scale-out: 60 seconds
- Scale-in: 300 seconds

These delays prevent frequent scaling changes
and help maintain service stability.
