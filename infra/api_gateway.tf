resource "aws_apigatewayv2_api" "task_api" {
  name          = "serverless-task-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["content-type"]
    allow_methods = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allow_origins = ["*"]
  }
}

resource "aws_apigatewayv2_integration" "task_api" {
  api_id                 = aws_apigatewayv2_api.task_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.task_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "tasks_collection" {
  api_id    = aws_apigatewayv2_api.task_api.id
  route_key = "ANY /tasks"
  target    = "integrations/${aws_apigatewayv2_integration.task_api.id}"
}

resource "aws_apigatewayv2_route" "tasks_item" {
  api_id    = aws_apigatewayv2_api.task_api.id
  route_key = "ANY /tasks/{taskId}"
  target    = "integrations/${aws_apigatewayv2_integration.task_api.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.task_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.task_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.task_api.execution_arn}/*/*"
}