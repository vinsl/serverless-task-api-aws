import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ["TASKS_TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)

ALLOWED_STATUSES = {"todo", "in_progress", "done"}
REQUIRED_CREATE_FIELDS = ("title", "content", "author")


def response(status_code, body=None):
    result = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        }
    }

    if body is not None:
        result["body"] = json.dumps(body)

    return result


def error(status_code, code, message):
    return response(
        status_code,
        {
            "error": code,
            "message": message
        }
    )


def parse_body(event):
    raw_body = event.get("body")

    if not raw_body:
        return None, error(400, "ValidationError", "Request body is required")

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        return None, error(400, "ValidationError", "Request body must be valid JSON")

    if not isinstance(body, dict):
        return None, error(400, "ValidationError", "Request body must be a JSON object")

    return body, None


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_task(event):
    body, body_error = parse_body(event)

    if body_error:
        return body_error

    missing_fields = [
        field
        for field in REQUIRED_CREATE_FIELDS
        if not isinstance(body.get(field), str) or not body[field].strip()
    ]

    if missing_fields:
        return error(
            400,
            "ValidationError",
            f"Required non-empty fields: {', '.join(missing_fields)}"
        )

    timestamp = utc_now()

    task = {
        "taskId": str(uuid.uuid4()),
        "title": body["title"].strip(),
        "content": body["content"].strip(),
        "author": body["author"].strip(),
        "status": "todo",
        "createdAt": timestamp,
        "updatedAt": timestamp
    }

    try:
        table.put_item(
            Item=task,
            ConditionExpression="attribute_not_exists(taskId)"
        )
    except ClientError:
        logger.exception("Unable to create task")
        return error(500, "InternalServerError", "Unable to create task")

    return response(201, task)


def list_tasks():
    try:
        result = table.scan()
        tasks = result.get("Items", [])
    except ClientError:
        logger.exception("Unable to list tasks")
        return error(500, "InternalServerError", "Unable to list tasks")

    return response(200, {"items": tasks, "count": len(tasks)})


def get_task(task_id):
    try:
        result = table.get_item(Key={"taskId": task_id})
    except ClientError:
        logger.exception("Unable to get task")
        return error(500, "InternalServerError", "Unable to get task")

    task = result.get("Item")

    if not task:
        return error(404, "NotFound", "Task not found")

    return response(200, task)


def update_task(event, task_id):
    body, body_error = parse_body(event)

    if body_error:
        return body_error

    allowed_fields = {"title", "content", "status"}
    updates = {
        key: value
        for key, value in body.items()
        if key in allowed_fields
    }

    if not updates:
        return error(
            400,
            "ValidationError",
            "Provide at least one field: title, content, status"
        )

    for field in ("title", "content"):
        if field in updates:
            if not isinstance(updates[field], str) or not updates[field].strip():
                return error(400, "ValidationError", f"{field} must be a non-empty string")
            updates[field] = updates[field].strip()

    if "status" in updates and updates["status"] not in ALLOWED_STATUSES:
        return error(
            400,
            "ValidationError",
            "status must be one of: todo, in_progress, done"
        )

    updates["updatedAt"] = utc_now()

    expression_parts = []
    expression_names = {}
    expression_values = {}

    for index, (field, value) in enumerate(updates.items()):
        name_key = f"#field{index}"
        value_key = f":value{index}"

        expression_parts.append(f"{name_key} = {value_key}")
        expression_names[name_key] = field
        expression_values[value_key] = value

    try:
        result = table.update_item(
            Key={"taskId": task_id},
            UpdateExpression=f"SET {', '.join(expression_parts)}",
            ConditionExpression="attribute_exists(taskId)",
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error(404, "NotFound", "Task not found")

        logger.exception("Unable to update task")
        return error(500, "InternalServerError", "Unable to update task")

    return response(200, result["Attributes"])


def delete_task(task_id):
    try:
        table.delete_item(
            Key={"taskId": task_id},
            ConditionExpression="attribute_exists(taskId)"
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error(404, "NotFound", "Task not found")

        logger.exception("Unable to delete task")
        return error(500, "InternalServerError", "Unable to delete task")

    return response(204)


def lambda_handler(event, context):
    request_context = event.get("requestContext", {})
    http = request_context.get("http", {})

    method = http.get("method")
    path = event.get("rawPath")
    path_parameters = event.get("pathParameters") or {}
    task_id = path_parameters.get("taskId")

    if not task_id and path.startswith("/tasks/"):
        task_id = path.removeprefix("/tasks/")

    logger.info("Request received: method=%s path=%s task_id=%s", method, path, task_id)

    if method == "POST" and path == "/tasks":
        return create_task(event)

    if method == "GET" and path == "/tasks":
        return list_tasks()

    if method == "GET" and task_id:
        return get_task(task_id)

    if method == "PATCH" and task_id:
        return update_task(event, task_id)

    if method == "DELETE" and task_id:
        return delete_task(task_id)

    return error(404, "NotFound", "Route not found")