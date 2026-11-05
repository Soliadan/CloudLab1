
# Cache Performance Analysis

## 1. Cache Implementation

The GET /orders endpoint uses the cache-aside strategy.

When a request arrives, the application first checks
the in-memory cache. If valid data is available,
the application returns it without querying PostgreSQL.

If the cache is empty or expired, the application
reads the data from PostgreSQL and stores it in
the cache for 60 seconds.

Configuration:
- Cache type: In-memory
- TTL: 60 seconds
- Strategy: Cache-aside
- Endpoint: GET /orders
- Cache toggle: CACHE_ENABLED


The k6 scenario used a mixed workload of POST and GET requests.

Each iteration included:
- 1 POST /orders request
- 3 GET /orders requests (cached endpoint)
- 6 GET /orders/{id} requests (not cached)

Therefore, only 30% of HTTP requests used the
cache-enabled endpoint.

The performance results represent the overall API,
not only the cached endpoint.

POST requests also continuously added new records,
which could affect database performance and cause
cached lists to become temporarily outdated.


## 2. Performance Comparison

The same k6 scenario was executed twice locally
with 20 virtual users for 10 minutes.

| Metric | Without cache | With cache |
|---|---:|---:|
| HTTP p95 latency | 55.93 ms | 76.86 ms |
| Requests per second | 123.98 | 116.31 |
| Database scans per 20 GET requests | 20 | 2 |
| Cache hit rate (separate 20-request test) | 0% | 90% |

The cache reduced database table scans by 90%
during the separate 20-request test.

However, the overall API latency increased by
approximately 37.4%, while throughput decreased
by approximately 6.2%.

Possible reasons include the low latency of the
local PostgreSQL database and the overhead of
cache synchronization.

## 3. Cache Hit Rate

A separate test sent 20 GET requests.

Results:
- Cache HIT: 18
- Cache MISS: 2
- Cache hit rate: 90%

The cache hit rate was calculated as:

Cache Hit Rate = HIT / (HIT + MISS) * 100%

Cache Hit Rate = 18 / 20 * 100% = 90%

## 4. Data Consistency

The cache TTL is 60 seconds.

After creating, updating, or deleting a record,
clients may receive outdated data from GET /orders
until the cached result expires.

The maximum stale-data period is approximately
60 seconds under the current implementation.

This period can be reduced by:
- Using a shorter TTL.
- Invalidating the cached list after successful
  POST, PUT, PATCH, or DELETE operations.

## 5. Limitations

The cache is stored in the memory of each
application process.

When multiple ECS containers or Gunicorn workers
are running, each process maintains its own cache.

This can cause:
- Different processes to return different data.
- Duplicate database queries.
- Inconsistent cache hit statistics.

A shared Redis cache would solve these problems
by providing centralized cached data across
all application instances.

## 6. Conclusion

The in-memory cache successfully reduced the
number of database reads.

Although it did not improve end-to-end latency
in the local performance test, it demonstrated
the cache-aside strategy and reduced database
load during repeated read operations.
