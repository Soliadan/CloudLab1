
# Separate ECS task for processing SQS messages

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = var.cpu
  memory = var.memory

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  execution_role_arn = aws_iam_role.execution.arn
  task_role_arn      = aws_iam_role.worker.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.main.repository_url}:${var.image_tag}"
      essential = true

      command = ["python", "worker.py"]

      environment = [
        {
          name  = "DB_HOST"
          value = aws_db_instance.main.address
        },
        {
          name  = "DB_NAME"
          value = "tasks_db"
        },
        {
          name  = "DB_USER"
          value = "tasks_user"
        },
        {
          name  = "DB_SSLMODE"
          value = "require"
        },
        {
          name  = "SQS_QUEUE_URL"
          value = aws_sqs_queue.orders.url
        },
        {
          name  = "AWS_REGION"
          value = var.region
        }
      ]

      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_db_instance.main.master_user_secret[0].secret_arn}:password::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "worker"
        }
      }
    }
  ])
}

# Separate ECS service without a load balancer

resource "aws_ecs_service" "worker" {
  name            = "${local.prefix}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn

  launch_type      = "FARGATE"
  platform_version = "1.4.0"

  # Do not start the worker before the Docker image is ready
  desired_count = 0

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [
    aws_iam_role_policy.worker_sqs,
    aws_iam_role_policy.execution,
    aws_vpc_security_group_ingress_rule.db,
    aws_vpc_security_group_egress_rule.app_db
  ]
}
