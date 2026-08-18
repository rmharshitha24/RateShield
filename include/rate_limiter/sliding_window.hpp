#pragma once
#include "rate_limiter/concepts.hpp"
#include <atomic>
#include <chrono>
#include <cstdint>

namespace rate_limiter {
// Fixed-window counter is a bounded, lock-free approximation of a sliding window.
class alignas(64) SlidingWindowCounter {
 public:
  SlidingWindowCounter(std::uint32_t limit, std::chrono::milliseconds window) noexcept : limit_{limit}, window_{window} {}
  Decision allow(std::chrono::steady_clock::time_point now, std::uint32_t cost = 1) noexcept {
    const auto epoch = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count() / window_.count());
    auto word = state_.load(std::memory_order_acquire);
    for (;;) {
      const auto old_epoch = word >> 32;
      const auto old_count = static_cast<std::uint32_t>(word);
      const auto count = old_epoch == epoch ? old_count : 0U;
      if (count > limit_ || cost > limit_ - count) return {false, count, now + window_};
      const std::uint64_t desired = (epoch << 32) | static_cast<std::uint64_t>(count + cost);
      if (state_.compare_exchange_weak(word, desired, std::memory_order_acq_rel)) return {true, limit_ - count - cost, now + window_};
    }
  }
 private:
  const std::uint32_t limit_; const std::chrono::milliseconds window_;
  std::atomic<std::uint64_t> state_{0}; // high 32: window epoch, low 32: count
};
static_assert(RateLimiterStrategy<SlidingWindowCounter>);
} // namespace rate_limiter
