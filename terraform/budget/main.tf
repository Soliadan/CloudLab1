# Existing resource: recover its original state OR import it. Never apply a create plan.
resource "aws_budgets_budget" "existing" {
  account_id        = var.account_id
  name              = "cloud-lab-budget"
  budget_type       = "COST"
  limit_amount      = "5"
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = var.time_period_start
  time_period_end   = var.time_period_end
  billing_view_arn  = var.billing_view_arn
  tags              = var.budget_tags

  cost_types {
    include_credit             = var.cost_types.include_credit
    include_discount           = var.cost_types.include_discount
    include_other_subscription = var.cost_types.include_other_subscription
    include_recurring          = var.cost_types.include_recurring
    include_refund             = var.cost_types.include_refund
    include_subscription       = var.cost_types.include_subscription
    include_support            = var.cost_types.include_support
    include_tax                = var.cost_types.include_tax
    include_upfront            = var.cost_types.include_upfront
    use_amortized              = var.cost_types.use_amortized
    use_blended                = var.cost_types.use_blended
  }
  dynamic "cost_filter" {
    for_each = var.cost_filters
    content {
      name   = cost_filter.key
      values = cost_filter.value
    }
  }
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 20
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_email_addresses
  }
  lifecycle {
    prevent_destroy = true
    precondition {
      condition     = var.adoption_reviewed
      error_message = "STOP: recover the original state or obtain approval to import cloud-lab-budget. Do not apply a create/update plan."
    }
  }
}
