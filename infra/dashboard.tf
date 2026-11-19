
resource "aws_cloudwatch_dashboard" "lab2" {
  dashboard_name = "${local.prefix}-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ECS Tasks: Desired vs Running"
          region = var.region
          period = 60
          metrics = [
            ["ECS/ContainerInsights", "DesiredTaskCount",
              "ClusterName", local.prefix,
              "ServiceName", local.prefix,
            { stat = "Average", label = "Desired" }],
            ["ECS/ContainerInsights", "RunningTaskCount",
              "ClusterName", local.prefix,
              "ServiceName", local.prefix,
            { stat = "Average", label = "Running" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "CPU Utilization"
          region = var.region
          period = 60
          metrics = [
            ["AWS/ECS", "CPUUtilization",
              "ClusterName", local.prefix,
              "ServiceName", local.prefix,
            { stat = "Average" }]
          ]
          annotations = {
            horizontal = [
              { value = 60, label = "CPU Target 60%" }
            ]
          }
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Requests per Minute"
          region = var.region
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "RequestCount",
              "LoadBalancer", aws_lb.main.arn_suffix,
            { stat = "Sum" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Response Time p95"
          region = var.region
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime",
              "LoadBalancer", aws_lb.main.arn_suffix,
            { stat = "p95" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "HTTP 5xx Errors"
          region = var.region
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count",
              "LoadBalancer", aws_lb.main.arn_suffix,
            { stat = "Sum", label = "Application 5xx" }],
            ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count",
              "LoadBalancer", aws_lb.main.arn_suffix,
            { stat = "Sum", label = "ALB 5xx" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "SQS Queue Length"
          region = var.region
          period = 60
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible",
              "QueueName", aws_sqs_queue.orders.name,
            { stat = "Average", label = "Waiting messages" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "Worker Tasks"
          region = var.region
          period = 60
          metrics = [
            ["ECS/ContainerInsights", "DesiredTaskCount",
              "ClusterName", aws_ecs_cluster.main.name,
              "ServiceName", aws_ecs_service.worker.name,
            { stat = "Average", label = "Desired workers" }],
            ["ECS/ContainerInsights", "RunningTaskCount",
              "ClusterName", aws_ecs_cluster.main.name,
              "ServiceName", aws_ecs_service.worker.name,
            { stat = "Average", label = "Running workers" }]
          ]
        }
      }
    ]
  })
}
