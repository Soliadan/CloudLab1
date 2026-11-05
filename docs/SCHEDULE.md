# Scheduled Scaling

## 1. Configuration

Scheduled scaling was implemented for the AWS ECS Fargate service using Terraform.

- AWS region: eu-north-1 (Stockholm)
- Timezone: Europe/Kyiv
- Daytime: 08:00–20:00 — minimum 2 ECS tasks
- Nighttime: 20:00–08:00 — minimum 1 ECS task
- Maximum tasks: 3
- CPU target: 60%

The scheduled actions are defined in `infra/scheduled_scaling.tf`.

Automatic CPU-based scaling remains enabled.

## 2. Terraform Implementation

Two scheduled actions were created:

- `cloudlab1-lab-day-scaling` — at 08:00, sets the minimum capacity to 2 tasks.
- `cloudlab1-lab-night-scaling` — at 20:00, sets the minimum capacity to 1 task.

Both actions use the Europe/Kyiv timezone.

Terraform successfully applied the configuration:

`Apply complete! Resources: 2 added, 0 changed, 0 destroyed.`

The actions were verified using the AWS CLI. Both schedules were present with the correct minimum capacities.

Actual execution at the scheduled times has not yet been observed.

## 3. Monthly Cost Calculation

The ECS task definition uses:

- CPU: 256 units (0.25 vCPU)
- Memory: 512 MiB (0.5 GiB)
- Operating system: Linux
- Architecture: x86-64

Estimated AWS Fargate on-demand prices in eu-north-1:

- vCPU: $0.04450 per vCPU-hour
- Memory: $0.00490 per GiB-hour

Hourly cost of one task:

`0.25 × 0.04450 + 0.5 × 0.00490 = $0.013575`

For this calculation, one month is assumed to contain 30 days.

### Without Scheduled Scaling

Assuming 2 tasks run continuously:

`2 × 24 × 30 = 1,440 task-hours`

Monthly cost:

`1,440 × $0.013575 = $19.55`

### With Scheduled Scaling

Daytime:

`2 × 12 × 30 = 720 task-hours`

Nighttime:

`1 × 12 × 30 = 360 task-hours`

Total:

`720 + 360 = 1,080 task-hours`

Monthly cost:

`1,080 × $0.013575 = $14.66`

## 4. Estimated Savings

| Metric | Without Schedule (2 Tasks Always) | With Schedule |
|---|---:|---:|
| Daytime minimum tasks | 2 | 2 |
| Nighttime minimum tasks | 2 | 1 |
| Monthly task-hours | 1,440 | 1,080 |
| Estimated Fargate cost | $19.55 | $14.66 |

Estimated monthly savings:

`$19.55 - $14.66 = $4.89`

Percentage savings:

`360 / 1,440 × 100 = 25%`

The scheduled configuration reduces baseline Fargate task-hours by 25% compared with running two tasks continuously.

Compared with the original configuration of one task running continuously, the new schedule increases the baseline Fargate cost by approximately $4.89 per 30-day month.

These calculations assume that no additional tasks are launched by CPU-based autoscaling. Actual costs may differ.

The estimate excludes other AWS resources, such as the load balancer, database, NAT Gateway, and CloudWatch.

## 5. Conclusion

Scheduled scaling was successfully configured in Terraform and verified in AWS.

During the day, the ECS service is configured to maintain at least 2 tasks. During the night, the minimum is reduced to 1 task.

Compared with keeping 2 tasks running continuously, this configuration can reduce baseline Fargate compute costs by approximately 25%.

Scaling to zero was not configured, so measuring a cold-start response time is not required.

Pricing reference: https://aws.amazon.com/fargate/pricing/
