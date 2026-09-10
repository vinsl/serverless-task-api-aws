output "api_endpoint" {
  description = "Public endpoint of the HTTP API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}