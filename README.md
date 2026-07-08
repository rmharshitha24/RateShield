# RateShield

RateShield is a production-style Flask backend for API rate limiting. It uses SQLAlchemy ORM with MySQL, dotenv configuration, structured JSON responses, request logging, and a Strategy Pattern implementation for four rate limiting algorithms.

## Highlights

- API key based request protection
- Per-user and per-endpoint rate limit rules
- Four rate limiting algorithms using the Strategy Pattern
- Request logs and usage statistics
- MySQL persistence with SQLAlchemy ORM
- Docker Compose setup for easy local running
- Pytest coverage for the main API flow

## Architecture

```text
Client
  |
  | X-API-Key
  v
Flask before_request middleware
  |
  +--> UserService: validate API key
  +--> RateLimitService: resolve user/endpoint policy
  +--> StrategyFactory
        |
        +--> Fixed Window Counter
        +--> Sliding Window Log
        +--> Token Bucket
        +--> Leaky Bucket
  |
  +--> protected route or HTTP 429
  |
  v
Flask after_request middleware
  |
  +--> RequestLogs table + Python logging
```

## Database Schema

`users`

| Column | Type | Notes |
| --- | --- | --- |
| id | INT | Primary key |
| username | VARCHAR(120) | Unique |
| api_key | VARCHAR(128) | Unique API credential |
| plan | VARCHAR(50) | User plan label |
| created_at | DATETIME | UTC creation time |

`rate_limit_rules`

| Column | Type | Notes |
| --- | --- | --- |
| id | INT | Primary key |
| user_id | INT | FK to users |
| endpoint | VARCHAR(255), nullable | Null means default rule for the user |
| algorithm | VARCHAR(50) | fixed_window, sliding_window_log, token_bucket, leaky_bucket |
| max_requests | INT | Request quota |
| time_window | INT | Window size in seconds |
| refill_rate | FLOAT | Tokens or leaks per second |
| bucket_capacity | INT | Capacity for bucket algorithms |

`request_logs`

| Column | Type | Notes |
| --- | --- | --- |
| id | INT | Primary key |
| user_id | INT, nullable | FK to users |
| endpoint | VARCHAR(255) | Request path |
| timestamp | DATETIME | UTC request time |
| allowed | BOOLEAN | Decision |
| algorithm | VARCHAR(50) | Strategy used |
| response_time_ms | FLOAT | Middleware latency |

`algorithm_states` stores persistent mutable state for fixed window, token bucket, and leaky bucket decisions.

## Algorithms

Fixed Window Counter: counts requests in a fixed interval. When the interval expires, the counter resets. Simple and fast, but bursts can happen around window boundaries.

Sliding Window Log: checks allowed request timestamps within the last `time_window` seconds. It is precise and smooth, with higher storage/query cost.

Token Bucket: tokens refill over time up to `bucket_capacity`; each request spends one token. It supports controlled bursts while enforcing an average rate.

Leaky Bucket: incoming requests fill a bucket that drains at `refill_rate`. If the bucket is full, new requests are rejected. This smooths traffic to a steady rate.

## Run Locally

1. Create a MySQL database:

```sql
CREATE DATABASE rateshield CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rateshield'@'localhost' IDENTIFIED BY 'rateshield';
GRANT ALL PRIVILEGES ON rateshield.* TO 'rateshield'@'localhost';
FLUSH PRIVILEGES;
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy environment settings:

```bash
cp .env.example .env
```

5. Run the app:

```bash
python main.py
```

The app starts on `http://localhost:5000`.

## Run With Docker

If Docker Desktop is installed, this is the easiest way to run both Flask and MySQL:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:5000
```

Stop the containers with:

```bash
docker compose down
```

To also remove the MySQL volume:

```bash
docker compose down -v
```

## Demo Flow

1. Start the server.
2. Create a user with a rate limit rule.
3. Copy the returned API key.
4. Call `/protected` with `X-API-Key`.
5. Send requests quickly until the API returns `429 Too Many Requests`.
6. Check `/logs` and `/stats`.

PowerShell examples are available in `API_EXAMPLES.md`.

## Run Tests

Install dependencies first:

```bash
pip install -r requirements.txt
```

Run the test suite:

```bash
pytest
```

The tests use an in-memory SQLite database, so they do not require a local MySQL server.

## API Examples

Create a user:

```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","plan":"pro","rate_limit":{"algorithm":"token_bucket","max_requests":10,"time_window":60,"refill_rate":1,"bucket_capacity":10}}'
```

Call the protected endpoint:

```bash
curl http://localhost:5000/protected -H "X-API-Key: <api_key>"
```

Update a default user policy:

```bash
curl -X PUT http://localhost:5000/users/1/rate-limit \
  -H "Content-Type: application/json" \
  -d '{"algorithm":"sliding_window_log","max_requests":5,"time_window":30,"refill_rate":0,"bucket_capacity":5}'
```

Set a per-endpoint rule:

```bash
curl -X PUT http://localhost:5000/users/1/rate-limit \
  -H "Content-Type: application/json" \
  -d '{"endpoint":"/protected","algorithm":"leaky_bucket","max_requests":20,"time_window":60,"refill_rate":0.5,"bucket_capacity":10}'
```

View logs:

```bash
curl http://localhost:5000/logs?limit=50
```

View stats:

```bash
curl http://localhost:5000/stats
```

When the rate limit is exceeded, RateShield returns:

```json
{
  "success": false,
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Rate limit exceeded."
  }
}
```

The response includes `HTTP 429` and a `Retry-After` header.

## Folder Structure

```text
app/
  algorithms/   Strategy Pattern implementations
  database/     SQLAlchemy instance and reference schema
  middleware/   Flask request hooks for rate limiting
  models/       SQLAlchemy ORM models
  routes/       JSON API blueprints
  services/     Business logic and aggregation
  utils/        Errors, responses, and logging
  config.py     dotenv-backed configuration
main.py         Application entrypoint
requirements.txt
.env.example
README.md
Dockerfile
docker-compose.yml
API_EXAMPLES.md
tests/
```

## Thread Safety

RateShield uses a keyed in-process lock per `(user_id, endpoint, algorithm)` before mutating algorithm state. This prevents race conditions between simultaneous Flask worker threads in the same process. For multi-process or multi-host deployments, move this lock to a distributed primitive such as MySQL row locks, Redis locks, or a dedicated rate-limit datastore.

## Future Improvements

- Add Alembic migrations instead of `db.create_all`.
- Add admin authentication for user, log, and stats routes.
- Add pagination and filters for request logs.
- Add a small Postman collection.
- Use Redis for rate limit state in a distributed deployment.
