import time
import requests
import concurrent.futures


def load_test(api_url, endpoint, concurrency=200, requests_total=1000):
    results = {
        "success": 0,
        "errors": 0,
        "times": []
    }

    def do_request():
        start = time.perf_counter()
        try:
            r = requests.get(f"{api_url}{endpoint}", timeout=10)
            r.raise_for_status()
            elapsed = time.perf_counter() - start
            return True, elapsed
        except:
            return False, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(do_request) for _ in range(requests_total)]
        t0 = time.perf_counter()

        for f in futures:
            ok, t = f.result()
            if ok:
                results["success"] += 1
                results["times"].append(t)
            else:
                results["errors"] += 1

        total_time = time.perf_counter() - t0

    avg_time = (
        sum(results["times"]) / len(results["times"])
        if results["times"] else None
    )

    return {
        "concurrency": concurrency,
        "total_requests": requests_total,
        "success": results["success"],
        "errors": results["errors"],
        "avg_time": avg_time,
        "throughput_rps": results["success"] / total_time,
        "total_time": total_time,
    }


if __name__ == "__main__":
    API_URL = "https://book-recommender-production-3009.up.railway.app"  # monolith
    # API_URL = "https://app-production-7be6.up.railway.app"  # services
    res1 = load_test(API_URL, "/top_books?start_year=2000&end_year=2025&limit=50")
    print(res1)
    res2 = load_test(API_URL, "/books?title=harry")
    print(res2)
    res3 = load_test(API_URL, "/recommend/2767052")
    print(res3)
