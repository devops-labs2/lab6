import random
import time

from flask import Flask, Response, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = Flask(__name__)

REQUESTS = Counter(
    "app_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "app_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)
IN_PROGRESS = Gauge(
    "app_requests_in_progress",
    "Requests currently being processed",
)


@app.before_request
def start_timer():
    request.start_time = time.perf_counter()
    IN_PROGRESS.inc()


@app.after_request
def record_metrics(response):
    IN_PROGRESS.dec()
    if request.path == "/metrics":
        return response

    # Use the route template rather than the actual path so random URLs do not
    # create a new time series for every request.
    endpoint = request.url_rule.rule if request.url_rule else "unknown"
    LATENCY.labels(endpoint).observe(time.perf_counter() - request.start_time)
    REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
    return response


@app.route("/")
def index():
    return "Hello, monitoring!"


@app.route("/slow")
def slow():
    time.sleep(random.uniform(0.2, 2.0))
    return "Slow response"


@app.route("/error")
def error():
    if random.random() < 0.5:
        return "Internal error", 500
    return "Lucky this time"


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
