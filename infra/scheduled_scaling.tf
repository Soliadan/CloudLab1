
# Daytime: minimum 2 ECS tasks at 08:00 Kyiv time

resource "aws_appautoscaling_scheduled_action" "ecs_day" {
  name               = "${local.prefix}-day-scaling"
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension

  schedule = "cron(0 8 * * ? *)"
  timezone = "Europe/Kyiv"

  scalable_target_action {
    min_capacity = 2
  }
}

# Nighttime: minimum 1 ECS task at 20:00 Kyiv time

resource "aws_appautoscaling_scheduled_action" "ecs_night" {
  name               = "${local.prefix}-night-scaling"
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension

  schedule = "cron(0 20 * * ? *)"
  timezone = "Europe/Kyiv"

  scalable_target_action {
    min_capacity = 1
  }
}
