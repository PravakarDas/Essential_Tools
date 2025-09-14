import os
import sys

from rq import Connection, Worker
import redis


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = redis.from_url(redis_url)
    with Connection(connection=conn):
        w = Worker(["neonpdf"])  # default queue
        w.work(with_scheduler=True)


if __name__ == "__main__":
    # Ensure app package importable if needed by tasks
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    main()

