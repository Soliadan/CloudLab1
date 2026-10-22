output "ecr_repository_url" { value = aws_ecr_repository.main.repository_url }
output "ecs_cluster" { value = aws_ecs_cluster.main.name }
output "ecs_service" { value = aws_ecs_service.main.name }
output "task_definition" { value = aws_ecs_task_definition.main.arn }
output "github_role_arn" { value = var.enable_github_deployment ? aws_iam_role.github[0].arn : null }
output "alb_dns_name" { value = aws_lb.main.dns_name }
output "app_url" { value = "http://${aws_lb.main.dns_name}" }
output "database_endpoint" { value = aws_db_instance.main.endpoint }

output "private_subnet_ids" { value = aws_subnet.private[*].id }
output "app_security_group_id" { value = aws_security_group.app.id }
