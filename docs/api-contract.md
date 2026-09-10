# API Contract

Base path: `/tasks`

## Task model

```json
{
  "taskId": "uuid",
  "title": "Prepare AWS deployment",
  "description": "Deploy the serverless task API with Terraform .",
  "status": "todo",
  "createdAt": "2026-09-10T12:00:00Z",
  "updatedAt": "2026-09-10T12:00:00Z"
}
```

## Endpoints

| Method | Path | Purpose | Success response |
|---|---|---|---|
| POST | `/tasks` | Create a task | 201 Created |
| GET | `/tasks` | List all tasks | 200 OK |
| GET | `/tasks/{taskId}` | Get one task | 200 OK |
| PATCH | `/tasks/{taskId}` | Update a task | 200 OK |
| DELETE | `/tasks/{taskId}` | Delete a task | 204 No Content |

## Create task

### Request body

```json
{
  "title": "Prepare AWS deployment",
  "description": "Deploy the serverless task API with Terraform.",
  "status": "todo"
}
```

### Validation rules

- `title` is required and must contain between 1 and 120 characters.
- `description` is optional and must contain at most 500 characters.
- `status` is optional and defaults to `todo`.
- Allowed status values are `todo`, `in_progress`, and `done`.

## Error responses

| Situation | Status code |
|---|---|
| Invalid JSON or invalid request data | 400 Bad Request |
| Task not found | 404 Not Found |
| Unexpected server error | 500 Internal Server Error |