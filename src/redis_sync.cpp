#include "rate_limiter/redis_sync.hpp"
#include <hiredis/hiredis.h>
#include <chrono>
#include <charconv>
#include <thread>

namespace rate_limiter {
namespace { constexpr char kScript[] = "local n=redis.call('INCRBY',KEYS[1],ARGV[1]); if n==tonumber(ARGV[1]) then redis.call('PEXPIRE',KEYS[1],ARGV[2]) end; return n"; }
RedisSyncWorker::RedisSyncWorker(std::string endpoint, std::chrono::milliseconds interval) : endpoint_(std::move(endpoint)), interval_(interval) {}
RedisSyncWorker::~RedisSyncWorker() { stop(); }
void RedisSyncWorker::add_source(SpscSyncQueue<>& source) { sources_.push_back(&source); }
void RedisSyncWorker::start() { if (!worker_.joinable()) worker_ = std::thread(&RedisSyncWorker::run, this); }
void RedisSyncWorker::stop() noexcept { stopping_.store(true, std::memory_order_release); if (worker_.joinable()) worker_.join(); }
bool RedisSyncWorker::connect() noexcept { return true; }
void RedisSyncWorker::flush(redisContext* ctx) noexcept {
  SyncEvent event{}; std::size_t commands = 0;
  for (auto* source : sources_) while (source->try_pop(event)) {
    const auto key = "rl:" + std::to_string(event.key_hash);
    if (redisAppendCommand(ctx, "EVAL %s 1 %s %u %u", kScript, key.c_str(), event.permits, event.window_ms) != REDIS_OK) { healthy_.store(false); return; }
    ++commands;
  }
  for (std::size_t i = 0; i < commands; ++i) { void* reply = nullptr; if (redisGetReply(ctx, &reply) != REDIS_OK) { healthy_.store(false); return; } freeReplyObject(reply); }
}
void RedisSyncWorker::run() noexcept {
  const auto separator = endpoint_.rfind(':');
  const auto host = separator == std::string::npos ? endpoint_ : endpoint_.substr(0, separator);
  int port = 6379;
  if (separator != std::string::npos) {
    const auto port_text = std::string_view(endpoint_).substr(separator + 1);
    const auto [last, error] = std::from_chars(port_text.data(), port_text.data() + port_text.size(), port);
    if (error != std::errc{} || last != port_text.data() + port_text.size() || port < 1 || port > 65535) {
      healthy_.store(false); return; // invalid configuration: retain local-only operation
    }
  }
  while (!stopping_.load(std::memory_order_acquire)) {
    // hiredis is deliberately confined to this worker: request threads never block on Redis.
    auto* ctx = redisConnect(host.c_str(), port);
    if (!ctx || ctx->err) { if (ctx) redisFree(ctx); healthy_.store(false); std::this_thread::sleep_for(std::chrono::seconds(1)); continue; }
    healthy_.store(true); while (!stopping_.load(std::memory_order_acquire) && !ctx->err) { flush(ctx); std::this_thread::sleep_for(interval_); }
    healthy_.store(false); redisFree(ctx);
  }
}
} // namespace rate_limiter
