#include "rate_limiter/token_bucket.hpp"
#include <benchmark/benchmark.h>
#include <atomic>
#include <thread>
#include <vector>

static void TokenBucketSingleThread(benchmark::State& state) {
  rate_limiter::TokenBucket bucket(1'000'000'000U, 1'000'000'000U);
  for (auto _ : state) benchmark::DoNotOptimize(bucket.allow(std::chrono::steady_clock::now()));
  state.SetItemsProcessed(state.iterations());
}
BENCHMARK(TokenBucketSingleThread)->Unit(benchmark::kNanosecond);

static void TokenBucketContention(benchmark::State& state) {
  static rate_limiter::TokenBucket bucket(1'000'000'000U, 1'000'000'000U);
  for (auto _ : state) benchmark::DoNotOptimize(bucket.allow(std::chrono::steady_clock::now()));
  state.SetItemsProcessed(state.iterations());
}
BENCHMARK(TokenBucketContention)->Threads(1)->Threads(4)->Threads(16)->Unit(benchmark::kNanosecond);
BENCHMARK_MAIN();
