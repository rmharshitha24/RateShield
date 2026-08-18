cmake_minimum_required(VERSION 3.24)
project(distributed_api_rate_limiter VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
find_package(Threads REQUIRED)
find_package(Protobuf CONFIG REQUIRED)
find_package(gRPC CONFIG REQUIRED)
find_package(hiredis CONFIG REQUIRED)
find_package(benchmark CONFIG REQUIRED)

set(PROTO_FILE ${CMAKE_CURRENT_SOURCE_DIR}/proto/rate_limiter.proto)
add_custom_command(
  OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/rate_limiter.pb.cc ${CMAKE_CURRENT_BINARY_DIR}/rate_limiter.pb.h
         ${CMAKE_CURRENT_BINARY_DIR}/rate_limiter.grpc.pb.cc ${CMAKE_CURRENT_BINARY_DIR}/rate_limiter.grpc.pb.h
  COMMAND $<TARGET_FILE:protobuf::protoc>
  ARGS --grpc_out ${CMAKE_CURRENT_BINARY_DIR} --cpp_out ${CMAKE_CURRENT_BINARY_DIR}
       -I ${CMAKE_CURRENT_SOURCE_DIR}/proto --plugin=protoc-gen-grpc=$<TARGET_FILE:gRPC::grpc_cpp_plugin> ${PROTO_FILE}
  DEPENDS ${PROTO_FILE})

add_library(rate_limiter_proto
  ${CMAKE_CURRENT_BINARY_DIR}/rate_limiter.pb.cc
  ${CMAKE_CURRENT_BINARY_DIR}/rate_limiter.grpc.pb.cc)
target_include_directories(rate_limiter_proto PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
target_link_libraries(rate_limiter_proto PUBLIC gRPC::grpc++ protobuf::libprotobuf)

add_library(rate_limiter_redis src/redis_sync.cpp)
target_include_directories(rate_limiter_redis PUBLIC include)
target_link_libraries(rate_limiter_redis PUBLIC hiredis::hiredis Threads::Threads)
target_compile_options(rate_limiter_redis PRIVATE $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive-> $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic>)

add_executable(rate_limiter_server src/server.cpp)
target_include_directories(rate_limiter_server PRIVATE include ${CMAKE_CURRENT_BINARY_DIR})
target_link_libraries(rate_limiter_server PRIVATE rate_limiter_proto rate_limiter_redis gRPC::grpc++ Threads::Threads)

add_executable(rate_limiter_bench benchmarks/main_bench.cpp)
target_include_directories(rate_limiter_bench PRIVATE include)
target_link_libraries(rate_limiter_bench PRIVATE benchmark::benchmark Threads::Threads)
