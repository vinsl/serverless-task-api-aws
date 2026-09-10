provider "aws" {
  region = "eu-west-3"

  default_tags {
    tags = {
      Project     = "serverless-task-api-aws"
      ManagedBy   = "Terraform"
      Environment = "demo"
    }
  }
}