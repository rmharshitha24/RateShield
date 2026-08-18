#pragma once
#include "rate_limiter/l1_cache.hpp"
#include <atomic>
#include <chrono>
#include <string>
#include <thread>
#include <vector>

struct redisContext;
namespace rate_limiter {
class RedisSyncWorker {
 public:
  explicit RedisSyncWorker(std::string endpoint, std::chrono::milliseconds interval = std::chrono::milliseconds(20));
  ~RedisSyncWorker();
  RedisSyncWorker(const RedisSyncWorker&) = delete;
  void add_source(SpscSyncQueue<>& source); // call during startup, before start()
  void start(); void stop() noexcept;
  [[nodiscard]] bool healthy() const noexcept { return healthy_.load(std::memory_order_relaxed); }
 private:
  void run() noexcept; bool connect() noexcept; void flush(redisContext*) noexcept;
  std::string endpoint_; std::chrono::milliseconds interval_; std::vector<SpscSyncQueue<>*> sources_;
  std::atomic<bool> stopping_{false}, healthy_{false}; std::thread worker_;
};
} // namespace rate_limiter
