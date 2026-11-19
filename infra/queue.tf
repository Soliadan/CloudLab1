
resource "aws_sqs_queue" "orders" {
  name                       = "${local.prefix}-orders-queue"
  visibility_timeout_seconds = 120
  receive_wait_time_seconds  = 20
}

# Allow Flask API to send messages to SQS

resource "aws_iam_role_policy" "api_sqs_send" {
  name = "${local.prefix}-api-sqs-send"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.orders.arn
      }
    ]
  })
}

# IAM role for the separate SQS worker

resource "aws_iam_role" "worker" {
  name               = "${local.prefix}-worker-task"
  assume_role_policy = aws_iam_role.execution.assume_role_policy
}

# Allow the worker to receive and process SQS messages

resource "aws_iam_role_policy" "worker_sqs" {
  name = "${local.prefix}-worker-sqs"
  role = aws_iam_role.worker.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.orders.arn
      }
    ]
  })
}
