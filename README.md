# RateShield — Distributed API Rate Limiter

A C++20 prototype for low-latency API rate limiting with local atomic decisions and asynchronous Redis counter synchronization.

## Overview

RateShield separates the request-time rate-limit decision from distributed counter synchronization:

- **L1:** Local in-memory rate checking using atomic operations.
- **L2:** Background Redis synchronization using pipelined Lua updates.
- **API:** Asynchronous gRPC service using CompletionQueue.
- **Goal:** Keep Redis and blocking coordination out of the local rate-check path.

> This is a local-first, eventually reconciled design. Redis is used for asynchronous counter synchronization; it is not currently a strict globally consistent quota enforcer.

## Features

- C++20 rate-limiting strategy interface using concepts.
- Token Bucket, Sliding Window Counter, and GCRA implementations.
- Atomic Token Bucket checks with no mutex in the local limiter path.
- Fixed-capacity key registry to avoid map allocation during local lookup.
- Lock-free single-producer/single-consumer queue for counter handoff.
- Cache-line padding with `alignas(64)` to reduce false sharing.
- Async gRPC rate-check endpoint with 200/429-style response fields.
- Redis Lua batching every 20 ms through hiredis pipelining.
- Local rate checks continue when Redis is unavailable.
- Google Benchmark workloads for local throughput and contention testing.

## Architecture

```text
Client
  |
  v
Async gRPC Server
  |
  v
L1 Local Engine
  |-- Fixed-capacity key lookup
  |-- Atomic Token Bucket decision
  |
  +--> SPSC Sync Queue --> Redis Background Worker --> Redis Lua Counter Update
```

## Project Structure

```text
.
├── benchmarks/
│   └── main_bench.cpp
├── include/rate_limiter/
│   ├── concepts.hpp
│   ├── token_bucket.hpp
│   ├── sliding_window.hpp
│   ├── gcra.hpp
│   ├── l1_cache.hpp
│   └── redis_sync.hpp
├── proto/
│   └── rate_limiter.proto
├── src/
│   ├── server.cpp
│   └── redis_sync.cpp
├── CMakeLists.txt
└── README.md
```

## Rate-Limiting Strategies

| Strategy | Use case | Status |
|---|---|---|
| Token Bucket | APIs that allow short bursts while enforcing an average rate | Used by the current gRPC server |
| Sliding Window Counter | Simple fixed-window quotas | Implemented as a strategy class |
| GCRA | Evenly spaced request traffic | Implemented as a strategy class |

All strategies implement the C++20 `RateLimiterStrategy` interface.

## Prerequisites

- CMake 3.24+
- C++20-compatible compiler
- gRPC
- Protobuf
- hiredis
- Google Benchmark
- Redis server

## Build

```bash
cmake -S . -B build
cmake --build build --config Release
```

## Run

Start Redis:

```bash
redis-server
```

Start RateShield:

```bash
./build/Release/rate_limiter_server 0.0.0.0:50051 127.0.0.1:6379
```

Arguments:

```text
rate_limiter_server <grpc-address> <redis-host:port>
```

Default values:

```text
gRPC address: 0.0.0.0:50051
Redis address: 127.0.0.1:6379
```

## API Response

The gRPC service returns:

```text
allowed
status_code
limit
remaining
reset_unix_ms
rate_limit_limit
rate_limit_remaining
rate_limit_reset
```

A rejected request returns `allowed = false` with a `429`-equivalent status code.

## Benchmarking

Build and run the benchmark executable:

```bash
./build/Release/rate_limiter_bench
```

The benchmark suite includes:

- Single-thread Token Bucket evaluation.
- Multi-thread contention testing with 1, 4, and 16 threads.

## Design Trade-offs

The service prioritizes low local latency and availability:

- Local requests do not synchronously wait for Redis.
- Redis failures do not stop local rate decisions.
- Counter updates may be delayed or dropped if the bounded queue is full.
- Multiple nodes can temporarily exceed a strict global quota.

For billing, security-sensitive, or globally strict limits, a future version should use Redis-authoritative Lua checks or leased token quotas.

## Future Improvements

- Runtime strategy selection through configuration.
- True weighted sliding-window implementation.
- Multi-CompletionQueue worker support with one SPSC queue per worker.
- Prometheus/OpenTelemetry metrics.
- Redis TLS, ACL support, timeouts, and circuit breaking.
- Integration tests, load tests, and sanitizer-based concurrency testing.
- Strict global quota mode using Redis-authoritative checks.

## Tech Stack

**C++20 · gRPC · Protocol Buffers · Redis · Lua · hiredis · CMake · Google Benchmark**
