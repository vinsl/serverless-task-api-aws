# Serverless Task API on AWS

A serverless REST API for managing tasks, built with AWS services and Python.

## Stack

- Amazon API Gateway
- AWS Lambda (Python)
- Amazon DynamoDB
- AWS IAM
- Amazon CloudWatch
- AWS SAM
- GitHub Actions

## Project goals

This project demonstrates how to design, deploy and operate a small serverless API on AWS using Infrastructure as Code.

The API will support core task-management operations:

- Create a task
- List tasks
- Get a task by ID
- Update a task
- Delete a task

## Planned architecture

```text
Client
  |
Amazon API Gateway
  |
AWS Lambda (Python)
  |
Amazon DynamoDB

CloudWatch: logs and metrics
IAM: least-privilege access control
```

## Status

Work in progress.

## License

MIT
