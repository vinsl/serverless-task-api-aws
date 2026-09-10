import importlib
import json
import os
from unittest.mock import MagicMock

os.environ.setdefault("TASKS_TABLE_NAME", "tasks-test")

from src import app

importlib.reload(app)


def make_event(method, path, body=None, task_id=None):
    return {
        "rawPath": path,
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": {"taskId": task_id} if task_id else None,
        "requestContext": {
            "http": {
                "method": method
            }
        },
    }


def body_of(result):
    return json.loads(result["body"])


def valid_task_payload():
    return {
        "title": "Préparer entretien Cloud Engineer",
        "content": "Réviser Terraform et AWS Lambda",
        "author": "vincent",
    }


def test_create_task_returns_201_and_writes_to_dynamodb(monkeypatch):
    fake_table = MagicMock()
    monkeypatch.setattr(app, "table", fake_table)

    result = app.lambda_handler(
        make_event("POST", "/tasks", valid_task_payload()),
        None,
    )

    payload = body_of(result)

    assert result["statusCode"] == 201
    assert payload["title"] == "Préparer entretien Cloud Engineer"
    assert payload["content"] == "Réviser Terraform et AWS Lambda"
    assert payload["author"] == "vincent"
    assert payload["status"] == "todo"
    assert payload["taskId"]
    assert payload["createdAt"]
    assert payload["updatedAt"] == payload["createdAt"]

    fake_table.put_item.assert_called_once()

    call_arguments = fake_table.put_item.call_args.kwargs

    assert call_arguments["Item"]["taskId"] == payload["taskId"]
    assert call_arguments["ConditionExpression"] == "attribute_not_exists(taskId)"


def test_create_task_without_body_returns_400(monkeypatch):
    monkeypatch.setattr(app, "table", MagicMock())

    result = app.lambda_handler(make_event("POST", "/tasks"), None)

    assert result["statusCode"] == 400
    assert body_of(result)["error"] == "ValidationError"
    assert body_of(result)["message"] == "Request body is required"


def test_create_task_with_missing_required_field_returns_400(monkeypatch):
    monkeypatch.setattr(app, "table", MagicMock())

    invalid_payload = {
        "title": "Préparer entretien",
        "author": "vincent",
    }

    result = app.lambda_handler(
        make_event("POST", "/tasks", invalid_payload),
        None,
    )

    assert result["statusCode"] == 400
    assert body_of(result)["error"] == "ValidationError"
    assert "content" in body_of(result)["message"]


def test_create_task_with_empty_title_returns_400(monkeypatch):
    monkeypatch.setattr(app, "table", MagicMock())

    invalid_payload = valid_task_payload()
    invalid_payload["title"] = "   "

    result = app.lambda_handler(
        make_event("POST", "/tasks", invalid_payload),
        None,
    )

    assert result["statusCode"] == 400
    assert body_of(result)["error"] == "ValidationError"
    assert "title" in body_of(result)["message"]


def test_list_tasks_returns_items(monkeypatch):
    fake_table = MagicMock()
    fake_table.scan.return_value = {
        "Items": [
            {
                "taskId": "task-1",
                "title": "Task 1",
                "content": "Content 1",
                "author": "vincent",
                "status": "todo",
            }
        ]
    }

    monkeypatch.setattr(app, "table", fake_table)

    result = app.lambda_handler(make_event("GET", "/tasks"), None)

    payload = body_of(result)

    assert result["statusCode"] == 200
    assert payload["count"] == 1
    assert payload["items"][0]["taskId"] == "task-1"

    fake_table.scan.assert_called_once()


def test_get_task_returns_200_when_task_exists(monkeypatch):
    fake_table = MagicMock()
    fake_table.get_item.return_value = {
        "Item": {
            "taskId": "task-1",
            "title": "Task 1",
            "content": "Content 1",
            "author": "vincent",
            "status": "todo",
        }
    }

    monkeypatch.setattr(app, "table", fake_table)

    result = app.lambda_handler(
        make_event("GET", "/tasks/task-1", task_id="task-1"),
        None,
    )

    assert result["statusCode"] == 200
    assert body_of(result)["taskId"] == "task-1"

    fake_table.get_item.assert_called_once_with(
        Key={"taskId": "task-1"}
    )


def test_get_task_returns_404_when_task_does_not_exist(monkeypatch):
    fake_table = MagicMock()
    fake_table.get_item.return_value = {}

    monkeypatch.setattr(app, "table", fake_table)

    result = app.lambda_handler(
        make_event("GET", "/tasks/missing", task_id="missing"),
        None,
    )

    assert result["statusCode"] == 404
    assert body_of(result)["error"] == "NotFound"


def test_update_task_returns_updated_item(monkeypatch):
    fake_table = MagicMock()
    fake_table.update_item.return_value = {
        "Attributes": {
            "taskId": "task-1",
            "title": "Task 1",
            "content": "Content 1",
            "author": "vincent",
            "status": "done",
            "createdAt": "2026-09-10T19:20:00+00:00",
            "updatedAt": "2026-09-10T19:25:00+00:00",
        }
    }

    monkeypatch.setattr(app, "table", fake_table)

    result = app.lambda_handler(
        make_event(
            "PATCH",
            "/tasks/task-1",
            body={"status": "done"},
            task_id="task-1",
        ),
        None,
    )

    assert result["statusCode"] == 200
    assert body_of(result)["status"] == "done"

    fake_table.update_item.assert_called_once()

    call_arguments = fake_table.update_item.call_args.kwargs

    assert call_arguments["Key"] == {"taskId": "task-1"}
    assert call_arguments["ConditionExpression"] == "attribute_exists(taskId)"
    assert call_arguments["ReturnValues"] == "ALL_NEW"


def test_update_task_with_invalid_status_returns_400(monkeypatch):
    monkeypatch.setattr(app, "table", MagicMock())

    result = app.lambda_handler(
        make_event(
            "PATCH",
            "/tasks/task-1",
            body={"status": "cancelled"},
            task_id="task-1",
        ),
        None,
    )

    assert result["statusCode"] == 400
    assert body_of(result)["error"] == "ValidationError"


def test_delete_task_returns_204(monkeypatch):
    fake_table = MagicMock()
    monkeypatch.setattr(app, "table", fake_table)

    result = app.lambda_handler(
        make_event("DELETE", "/tasks/task-1", task_id="task-1"),
        None,
    )

    assert result["statusCode"] == 204
    assert "body" not in result

    fake_table.delete_item.assert_called_once_with(
        Key={"taskId": "task-1"},
        ConditionExpression="attribute_exists(taskId)",
    )


def test_unknown_route_returns_404(monkeypatch):
    monkeypatch.setattr(app, "table", MagicMock())

    result = app.lambda_handler(
        make_event("GET", "/unknown"),
        None,
    )

    assert result["statusCode"] == 404
    assert body_of(result)["error"] == "NotFound"