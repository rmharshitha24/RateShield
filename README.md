# Distributed API Rate Limiter (C++20)

This is a bounded-memory, asynchronous rate limiter designed around an L1 local decision path and a Redis L2 reconciliation path. The `allow()` implementations allocate no memory and use no mutexes. The gRPC server uses a single CompletionQueue producer for its SPSC counter queue; scale with one process per CPU core or extend the server with one queue per CompletionQueue worker.

## Build

Install CMake 3.24+, a C++20 compiler, Protobuf, gRPC, hiredis, and Google Benchmark (for example through vcpkg). Then configure and build:

```powershell
cmake -S . -B build
cmake --build build --config Release
```

Run the server with optional listen and Redis addresses:

```powershell
.\build\Release\rate_limiter_server.exe 0.0.0.0:50051 127.0.0.1:6379
```

The Redis Lua script is pipelined every 20 ms. If Redis disconnects, the L1 limiter remains available (degraded, locally enforced mode); queued updates are bounded and dropped rather than adding latency. Export `RedisSyncWorker::healthy()` into the service's health/metrics endpoint in a deployment.

## Policy model and operational notes

The sample server uses a deployment-owned 1,000 req/s token-bucket policy. In a real control plane, resolve an authenticated tenant to a precompiled policy before calling the limiter; never trust client-supplied limits. The request protocol keeps `limit` and `window_ms` for a policy-aware gateway to populate, but the sample intentionally does not accept them as authority.

For strict multi-region limits, an asynchronous L2 is necessarily an approximation: nodes can overshoot by their local burst plus unflushed events. Put highly sensitive quotas through a Redis-authoritative Lua check, or allocate each node a leased quota. Use Redis ACLs, TLS/stunnel, timeouts, and metrics (queue drops, Redis health, rejected checks) in production.
