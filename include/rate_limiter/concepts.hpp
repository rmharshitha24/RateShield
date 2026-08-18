#pragma once
#include <chrono>
#include <concepts>
#include <cstdint>

namespace rate_limiter {
struct Decision { bool allowed; std::uint32_t remaining; std::chrono::steady_clock::time_point reset; };

// Algorithms are interchangeable only when their hot-path contract is met at compile time.
template <class T>
concept RateLimiterStrategy = requires(T limiter, std::chrono::steady_clock::time_point now, std::uint32_t cost) {
  { limiter.allow(now, cost) } noexcept -> std::same_as<Decision>;
};
} // namespace rate_limiter
