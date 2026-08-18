#pragma once
#include "rate_limiter/concepts.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>

namespace rate_limiter {
// One atomic word makes the decision linearizable without a mutex or allocation.
class alignas(64) TokenBucket {
 public:
  TokenBucket(std::uint32_t capacity, std::uint32_t refill_per_second) noexcept
      : capacity_{capacity}, refill_per_second_{refill_per_second}, tokens_{capacity}, last_ns_{now_ns()} {}
  Decision allow(std::chrono::steady_clock::time_point now, std::uint32_t cost = 1) noexcept {
    const auto ns = to_ns(now);
    auto observed_last = last_ns_.load(std::memory_order_relaxed);
    while (ns > observed_last && !last_ns_.compare_exchange_weak(observed_last, ns, std::memory_order_acq_rel)) {}
    if (ns > observed_last) {
      const auto added = ((ns - observed_last) * refill_per_second_) / 1'000'000'000ULL;
      auto old = tokens_.load(std::memory_order_relaxed);
      while (!tokens_.compare_exchange_weak(old, std::min<std::uint64_t>(capacity_, old + added), std::memory_order_acq_rel)) {}
    }
    auto current = tokens_.load(std::memory_order_relaxed);
    while (current >= cost) {
      if (tokens_.compare_exchange_weak(current, current - cost, std::memory_order_acq_rel))
        return {true, static_cast<std::uint32_t>(current - cost), now + std::chrono::seconds(1)};
    }
    return {false, static_cast<std::uint32_t>(current), now + std::chrono::seconds(1)};
  }
 private:
  static std::uint64_t to_ns(std::chrono::steady_clock::time_point t) noexcept { return static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(t.time_since_epoch()).count()); }
  static std::uint64_t now_ns() noexcept { return to_ns(std::chrono::steady_clock::now()); }
  const std::uint32_t capacity_, refill_per_second_;
  std::atomic<std::uint64_t> tokens_;
  std::atomic<std::uint64_t> last_ns_;
};
static_assert(RateLimiterStrategy<TokenBucket>);
} // namespace rate_limiter
