variable "account_id" {
  description = "Verified account in which the state bucket will live."
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Provide a verified 12-digit state bucket owner account ID."
  }
}
variable "region" {
  type    = string
  default = "eu-north-1"
}
variable "bucket_name" {
  description = "Globally unique nonsecret name, e.g. cloudlab1-state-ACCOUNT-REGION."
  type        = string
  validation {
    condition     = length(var.bucket_name) >= 3 && length(var.bucket_name) <= 63 && can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.bucket_name))
    error_message = "Use 3..63 lowercase letters, numbers and hyphens."
  }
}
