#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <string_view>
#include <span>

namespace rate_limiter {
struct SyncEvent { std::uint64_t key_hash; std::uint32_t permits; std::uint32_t limit; std::uint32_t window_ms; };

// Exactly one producer and one consumer touch this ring; padding keeps their cache lines separate.
template <std::size_t Capacity = 4096>
class SpscSyncQueue {
  static_assert((Capacity & (Capacity - 1)) == 0, "capacity must be a power of two");
 public:
  bool try_push(const SyncEvent& event) noexcept {
    const auto head = head_.load(std::memory_order_relaxed);
    if (head - tail_.load(std::memory_order_acquire) == Capacity) return false;
    slots_[head & (Capacity - 1)] = event;
    head_.store(head + 1, std::memory_order_release); return true;
  }
  bool try_pop(SyncEvent& event) noexcept {
    const auto tail = tail_.load(std::memory_order_relaxed);
    if (tail == head_.load(std::memory_order_acquire)) return false;
    event = slots_[tail & (Capacity - 1)]; tail_.store(tail + 1, std::memory_order_release); return true;
  }
  // Useful to batch drain without allocating an intermediate container.
  std::size_t drain(std::span<SyncEvent> destination) noexcept {
    std::size_t n = 0; while (n < destination.size() && try_pop(destination[n])) ++n; return n;
  }
 private:
  std::array<SyncEvent, Capacity> slots_{};
  alignas(64) std::atomic<std::uint64_t> head_{0}; // avoids false sharing with consumer-owned tail
  alignas(64) std::atomic<std::uint64_t> tail_{0};
};
inline std::uint64_t stable_hash(std::string_view text) noexcept {
  std::uint64_t h = 1469598103934665603ULL; for (unsigned char c : text) { h ^= c; h *= 1099511628211ULL; } return h;
}
} // namespace rate_limiter
