variable "region" {
  type    = string
  default = "eu-north-1"
}
variable "name" {
  type    = string
  default = "cloudlab1"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,19}$", var.name))
    error_message = "Use 2..20 lowercase name characters; the ALB name must fit 32 characters with environment."
  }
}
variable "environment" {
  type    = string
  default = "lab"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,7}$", var.environment))
    error_message = "Use a short 1..8 character environment name."
  }
}
variable "cpu" {
  type    = number
  default = 256
  validation {
    condition     = contains([256, 512, 1024], var.cpu)
    error_message = "This lab permits 256/512/1024 CPU units; review cost before expanding the range."
  }
}
variable "memory" {
  type    = number
  default = 512
  validation {
    condition     = contains(lookup({ "256" = [512, 1024, 2048], "512" = [1024, 2048, 3072, 4096], "1024" = [2048, 3072, 4096, 5120, 6144, 7168, 8192] }, tostring(var.cpu), []), var.memory)
    error_message = "Select a supported Fargate CPU/memory pair (memory in MiB)."
  }
}
variable "desired_count" {
  type    = number
  default = 0
  validation {
    condition     = contains([0, 1, 2], var.desired_count)
    error_message = "This lab permits 0..2 tasks; more tasks require a reviewed cost/config change."
  }
}
variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}
variable "db_storage_gb" {
  type    = number
  default = 20
  validation {
    condition     = var.db_storage_gb >= 20 && var.db_storage_gb <= 100 && floor(var.db_storage_gb) == var.db_storage_gb
    error_message = "Choose an integer 20..100 GiB for the lab; review cost before increasing this limit."
  }
}
variable "image_tag" {
  description = "Tag of the actual API image to upload to this ECR before starting tasks."
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.image_tag)) && var.image_tag != "bootstrap"
    error_message = "Provide a real API image tag; upload it before setting desired_count above zero."
  }
}
variable "github_branch" {
  type    = string
  default = "main"
  validation {
    condition     = can(regex("^[A-Za-z0-9_./-]+$", var.github_branch))
    error_message = "Use an exact branch name without wildcard/colon subject characters."
  }
}
variable "existing_github_oidc_arn" {
  type    = string
  default = ""
}

variable "aws_account_id" {
  description = "Verified Sunrise Sprint PROJECT account ID, not an assumed management account ID."
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "Provide the verified 12-digit project account ID."
  }
}
variable "db_backup_retention_days" {
  type    = number
  default = 7
  validation {
    condition     = contains([1, 2, 3, 4, 5, 6, 7], var.db_backup_retention_days)
    error_message = "Keep 1..7 days of backups for this lab."
  }
}
variable "log_retention_days" {
  type    = number
  default = 7
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30], var.log_retention_days)
    error_message = "Choose a supported short retention period."
  }
}

variable "enable_github_deployment" {
  description = "Task 5: create the GitHub OIDC deployment role and its least-privilege policy."
  type        = bool
  default     = false
}
