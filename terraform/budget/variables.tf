variable "account_id" {
  description = "Account OWNING the existing budget, verified with STS and Budgets (may differ from the project account)."
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Provide the verified 12-digit budget owner account ID."
  }
}
variable "region" {
  type    = string
  default = "eu-north-1"
}
variable "budget_email_addresses" {
  description = "Exact existing EMAIL subscribers; obtain privately from AWS, never guess. Sensitive still appears in state."
  type        = set(string)
  sensitive   = true
  validation {
    condition     = length(var.budget_email_addresses) > 0 && length(var.budget_email_addresses) <= 10 && alltrue([for email in var.budget_email_addresses : can(regex("^[^ @]+@[^ @]+\\.[^ @]+$", email))])
    error_message = "Provide 1..10 existing email subscribers."
  }
}
variable "cost_types" {
  description = "Copy ALL cost flags from describe-budget; only IncludeCredit=true is confirmed. No guessed defaults."
  type = object({
    include_credit             = bool
    include_discount           = bool
    include_other_subscription = bool
    include_recurring          = bool
    include_refund             = bool
    include_subscription       = bool
    include_support            = bool
    include_tax                = bool
    include_upfront            = bool
    use_amortized              = bool
    use_blended                = bool
  })
  validation {
    condition     = var.cost_types.include_credit
    error_message = "Existing budget has IncludeCredit=true; changing it needs a separate approved code review."
  }
}
variable "cost_filters" {
  description = "Exact existing CostFilters. Empty only when the existing budget has no filters."
  type        = map(list(string))
  default     = {}
}
variable "budget_tags" {
  description = "Exact existing budget tags; inspect before adoption."
  type        = map(string)
  default     = {}
}
variable "time_period_start" {
  description = "Exact existing UTC start, YYYY-MM-DD_HH:mm."
  type        = string
}
variable "time_period_end" {
  description = "Exact existing UTC end; required to avoid the provider default silently changing it."
  type        = string
}
variable "billing_view_arn" {
  type    = string
  default = null
}
variable "adoption_reviewed" {
  description = "Safety gate: true only for an owner-approved import/recovered state and reviewed adoption plan. This is NOT an import detector."
  type        = bool
  default     = false
}
