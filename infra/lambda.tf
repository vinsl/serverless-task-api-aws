data "archive_file" "task_api" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/../dist/task-api.zip"
}

resource "aws_lambda_function" "task_api" {
  function_name = "serverless-task-api"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "app.lambda_handler"
  runtime       = "python3.12"
  timeout       = 10
  memory_size   = 128

  filename         = data.archive_file.task_api.output_path
  source_code_hash = data.archive_file.task_api.output_base64sha256

  environment {
    variables = {
      TASKS_TABLE_NAME = aws_dynamodb_table.tasks.name
    }
  }
}