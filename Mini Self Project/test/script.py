#!/usr/bin/env python3
import requests
import time
import concurrent.futures
from collections import Counter

# Configuration
base_url = "http://44.223.51.187:30887"  # Your worker node IP and port
total_requests = 1000000
batch_size = 5000  # Send 1000 requests concurrently
check_interval = 5  # seconds

# Initialize counters
pod_counter = Counter()
total_counted = 0
last_check_time = time.time()
start_time = time.time()


def send_request():
    try:
        response = requests.get(base_url, timeout=5)
        data = response.json()
        return data.get("pod")
    except Exception as e:
        return None


print(
    f"Starting stress test with {total_requests} requests using concurrency of {batch_size}..."
)

try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        while total_counted < total_requests:
            # Determine how many requests to send in this batch
            remaining = total_requests - total_counted
            current_batch_size = min(batch_size, remaining)

            # Submit batch of requests
            future_to_request = {
                executor.submit(send_request): i for i in range(current_batch_size)
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_request):
                pod_name = future.result()
                if pod_name:
                    pod_counter[pod_name] += 1
                    total_counted += 1

            # Print stats periodically
            current_time = time.time()
            elapsed = current_time - last_check_time

            if elapsed >= check_interval:
                elapsed_total = current_time - start_time
                rate = total_counted / elapsed_total if elapsed_total > 0 else 0

                print(
                    f"\nRequests sent so far: {total_counted} ({rate:.2f} requests/sec)"
                )
                print("Distribution by pod:")
                for pod, count in pod_counter.items():
                    percentage = (
                        (count / total_counted) * 100 if total_counted > 0 else 0
                    )
                    print(f"  {pod}: {count} requests ({percentage:.2f}%)")

                last_check_time = current_time

except KeyboardInterrupt:
    print("\nStress test stopped by user.")

# Final report
elapsed_total = time.time() - start_time
rate = total_counted / elapsed_total if elapsed_total > 0 else 0

print("\n=== Final Distribution Report ===")
print(f"Total requests sent: {total_counted}")
print(f"Time elapsed: {elapsed_total:.2f} seconds")
print(f"Average rate: {rate:.2f} requests/second")
print("\nDistribution by pod:")
for pod, count in sorted(pod_counter.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_counted) * 100 if total_counted > 0 else 0
    print(f"  {pod}: {count} requests ({percentage:.2f}%)")
