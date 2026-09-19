from __future__ import annotations

import argparse
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def one_request(url: str, timeout: float) -> tuple[float, bool]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            ok = 200 <= response.status < 400
    except (urllib.error.URLError, TimeoutError):
        ok = False
    return (time.perf_counter() - started) * 1000, ok


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percent)))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded read-only MigrateFlow load smoke test")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--path", default="/health")
    parser.add_argument("--users", type=int, default=25)
    parser.add_argument("--requests-per-user", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    parser.add_argument("--max-p95-ms", type=float, default=750.0)
    args = parser.parse_args()
    if not 1 <= args.users <= 10_000 or not 1 <= args.requests_per_user <= 1_000:
        parser.error("users must be 1..10000 and requests-per-user must be 1..1000")

    url = f"{args.base_url.rstrip('/')}/{args.path.lstrip('/')}"
    total = args.users * args.requests_per_user
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.users) as pool:
        futures = [pool.submit(one_request, url, args.timeout) for _ in range(total)]
        results = [future.result() for future in as_completed(futures)]
    elapsed = time.perf_counter() - started
    latencies = [latency for latency, _ in results]
    failures = sum(not ok for _, ok in results)
    error_rate = failures / total
    p95 = percentile(latencies, 0.95)
    print(
        f"requests={total} users={args.users} rps={total / elapsed:.2f} "
        f"mean_ms={statistics.fmean(latencies):.2f} p95_ms={p95:.2f} "
        f"errors={failures} error_rate={error_rate:.4f}"
    )
    return int(error_rate > args.max_error_rate or p95 > args.max_p95_ms)


if __name__ == "__main__":
    raise SystemExit(main())
