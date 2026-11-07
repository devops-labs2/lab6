import random
import sys
import threading
import time
import urllib.error
import urllib.request

URL = "http://localhost:5000"
# 60% normal requests, 20% slow requests, 20% requests that may fail.
PATHS = ["/"] * 6 + ["/slow"] * 2 + ["/error"] * 2


def worker(stop_at, stats, lock):
    while time.time() < stop_at:
        path = random.choice(PATHS)
        try:
            with urllib.request.urlopen(URL + path, timeout=10) as resp:
                code = resp.status
        except urllib.error.HTTPError as exc:
            code = exc.code
        except Exception:
            code = "fail"

        with lock:
            stats[code] = stats.get(code, 0) + 1
        time.sleep(random.uniform(0.05, 0.3))


def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    stats, lock = {}, threading.Lock()
    stop_at = time.time() + duration

    print(f"Навантаження: {threads} потоків, {duration} с")
    pool = [
        threading.Thread(target=worker, args=(stop_at, stats, lock))
        for _ in range(threads)
    ]
    for thread in pool:
        thread.start()
    for thread in pool:
        thread.join()
    print("Результат за кодами відповіді:", stats)


if __name__ == "__main__":
    main()
