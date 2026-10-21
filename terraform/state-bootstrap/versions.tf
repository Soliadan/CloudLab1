terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}
# Intentionally local for the FIRST bootstrap: the bucket does not exist yet.
# Keep this state private. For later migration see backend.tf.example and the runbook.
provider "aws" {
  region              = var.region
  allowed_account_ids = [var.account_id]
}
