#include "rate_limiter/l1_cache.hpp"
#include "rate_limiter/redis_sync.hpp"
#include "rate_limiter/token_bucket.hpp"
#include "rate_limiter.grpc.pb.h"
#include <array>
#include <atomic>
#include <csignal>
#include <cstdlib>
#include <grpcpp/grpcpp.h>
#include <grpcpp/alarm.h>
#include <iostream>
#include <memory>

namespace {
constexpr std::size_t kSlots = 65'536; // fixed capacity: no map allocation or lock in request evaluation
constexpr std::uint32_t kLimit = 1'000, kRefillPerSecond = 1'000;
std::atomic<bool> g_stop{false};
void on_signal(int) { g_stop.store(true, std::memory_order_release); }

struct KeySlot {
  std::atomic<std::uint64_t> hash{0};
  rate_limiter::TokenBucket limiter{kLimit, kRefillPerSecond};
};
class LocalEngine {
 public:
  rate_limiter::Decision allow_request(std::uint64_t hash, std::uint32_t cost) noexcept {
    // Open addressing bounds memory and avoids heap allocation. Hash zero is reserved as empty.
    hash = hash ? hash : 1;
    for (std::size_t probe = 0; probe < 32; ++probe) {
      auto& slot = slots_[(hash + probe) & (kSlots - 1)];
      auto expected = std::uint64_t{0};
      if (slot.hash.compare_exchange_strong(expected, hash, std::memory_order_acq_rel) || expected == hash)
        return slot.limiter.allow(std::chrono::steady_clock::now(), cost);
    }
    return {false, 0, std::chrono::steady_clock::now() + std::chrono::seconds(1)}; // table pressure: fail closed
  }
 private:
  std::array<KeySlot, kSlots> slots_;
};

class AsyncService final {
 public:
  AsyncService(std::string address, rate_limiter::RedisSyncWorker& redis, rate_limiter::SpscSyncQueue<>& sync_queue)
      : redis_(redis), sync_queue_(sync_queue) {
    grpc::ServerBuilder builder; builder.AddListeningPort(address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service_); cq_ = builder.AddCompletionQueue(); server_ = builder.BuildAndStart();
  }
  void run() {
    new Call(this); void* tag; bool ok;
    while (!g_stop.load(std::memory_order_acquire)) {
      const auto deadline = std::chrono::system_clock::now() + std::chrono::milliseconds(100);
      const auto result = cq_->AsyncNext(&tag, &ok, deadline);
      if (result == grpc::CompletionQueue::GOT_EVENT) static_cast<Call*>(tag)->proceed(ok);
      else if (result == grpc::CompletionQueue::SHUTDOWN) break;
    }
    shutdown();
  }
  void shutdown() { if (server_) server_->Shutdown(); if (cq_) cq_->Shutdown(); }
 private:
  class Call {
   public:
    explicit Call(AsyncService* owner) : owner_(owner), responder_(&context_) { proceed(true); }
    void proceed(bool ok) {
      if (state_ == Create) { state_ = Process; owner_->service_.RequestCheck(&context_, &request_, &responder_, owner_->cq_.get(), owner_->cq_.get(), this); return; }
      if (state_ == Process) {
        if (!ok) { delete this; return; }
        new Call(owner_);
        const auto key_hash = rate_limiter::stable_hash(request_.key());
        const auto cost = request_.cost() ? request_.cost() : 1U;
        const auto decision = owner_->engine_->allow_request(key_hash, cost);
        const auto now_system = std::chrono::system_clock::now();
        const auto reset_ms = std::chrono::duration_cast<std::chrono::milliseconds>(now_system.time_since_epoch()).count() + 1000;
        response_.set_allowed(decision.allowed); response_.set_status_code(decision.allowed ? 200 : 429);
        response_.set_limit(kLimit); response_.set_remaining(decision.remaining); response_.set_reset_unix_ms(reset_ms);
        response_.set_rate_limit_limit(std::to_string(kLimit)); response_.set_rate_limit_remaining(std::to_string(decision.remaining)); response_.set_rate_limit_reset(std::to_string(reset_ms / 1000));
        if (decision.allowed) owner_->sync_queue_.try_push({key_hash, cost, kLimit, 1000}); // full queue means bounded distributed-sync loss, never latency loss
        state_ = Finish; responder_.Finish(response_, grpc::Status::OK, this); return;
      }
      delete this;
    }
   private:
    enum State { Create, Process, Finish } state_{Create}; AsyncService* owner_;
    grpc::ServerContext context_; ratelimiter::v1::RateLimitRequest request_; ratelimiter::v1::RateLimitResponse response_;
    grpc::ServerAsyncResponseWriter<ratelimiter::v1::RateLimitResponse> responder_;
  };
  ratelimiter::v1::RateLimiter::AsyncService service_; std::unique_ptr<grpc::ServerCompletionQueue> cq_; std::unique_ptr<grpc::Server> server_;
  // The fixed table is intentionally heap-resident: keeping several MiB off the server thread's stack.
  std::unique_ptr<LocalEngine> engine_{std::make_unique<LocalEngine>()}; rate_limiter::RedisSyncWorker& redis_; rate_limiter::SpscSyncQueue<>& sync_queue_;
};
} // namespace

int main(int argc, char** argv) {
  std::signal(SIGINT, on_signal); std::signal(SIGTERM, on_signal);
  const std::string address = argc > 1 ? argv[1] : "0.0.0.0:50051";
  const std::string redis_endpoint = argc > 2 ? argv[2] : "127.0.0.1:6379";
  rate_limiter::SpscSyncQueue<> queue; rate_limiter::RedisSyncWorker redis(redis_endpoint); redis.add_source(queue); redis.start();
  std::cout << "rate limiter listening on " << address << " (Redis " << redis_endpoint << ")\n";
  AsyncService server(address, redis, queue); server.run(); redis.stop();
}
