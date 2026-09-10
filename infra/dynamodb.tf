resource "aws_dynamodb_table" "tasks" {
  name         = "serverless-task-api-tasks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "taskId"

  attribute {
    name = "taskId"
    type = "S"
  }

  tags = {
    Name = "serverless-task-api-tasks"
  }
}