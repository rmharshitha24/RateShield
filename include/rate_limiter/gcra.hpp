#pragma once
#include "rate_limiter/concepts.hpp"
#include <atomic>
#include <chrono>
#include <cstdint>

namespace rate_limiter {
class alignas(64) Gcra {
 public:
  Gcra(std::uint32_t rate_per_second, std::uint32_t burst) noexcept : interval_ns_{1'000'000'000ULL / rate_per_second}, burst_ns_{interval_ns_ * burst} {}
  Decision allow(std::chrono::steady_clock::time_point now, std::uint32_t cost = 1) noexcept {
    const auto n = ns(now); auto tat = tat_ns_.load(std::memory_order_acquire);
    for (;;) {
      if (n + burst_ns_ < tat) return {false, 0, now + std::chrono::nanoseconds(tat - n)};
      const auto next = (tat > n ? tat : n) + interval_ns_ * cost;
      if (tat_ns_.compare_exchange_weak(tat, next, std::memory_order_acq_rel)) return {true, 0, now + std::chrono::nanoseconds(next - n)};
    }
  }
 private:
  static std::uint64_t ns(std::chrono::steady_clock::time_point t) noexcept { return std::chrono::duration_cast<std::chrono::nanoseconds>(t.time_since_epoch()).count(); }
  const std::uint64_t interval_ns_, burst_ns_; std::atomic<std::uint64_t> tat_ns_{0};
};
static_assert(RateLimiterStrategy<Gcra>);
} // namespace rate_limiter
