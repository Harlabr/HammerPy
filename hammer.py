#!/usr/bin/env python3

import sys
import time
import threading
import argparse
import requests
from datetime import datetime
from collections import deque

VERSION = "1.0"
NAME = "HammerPy"

def get_ip_info():
    try:
        ip_resp = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip = ip_resp.json().get('ip')
        geo_resp = requests.get(f'http://ip-api.com/json/{ip}?fields=country,countryCode', timeout=5)
        geo = geo_resp.json()
        return ip, geo.get('country', 'Unknown')
    except Exception:
        return 'Unknown', 'Unknown'

class RequestWorker:
    def __init__(self, url, delay, stats, stop_event, worker_id):
        self.url = url
        self.delay = delay
        self.stats = stats
        self.stop_event = stop_event
        self.id = worker_id
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.running = False

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.stop_event.set()

    def run(self):
        session = requests.Session()
        while self.running and not self.stop_event.is_set():
            try:
                start = time.time()
                resp = session.get(self.url, timeout=10)
                elapsed = time.time() - start
                success = resp.status_code < 400
                status_code = resp.status_code
            except Exception as e:
                success = False
                status_code = str(e)
                elapsed = 0
            self.stats.add_result(success, status_code, elapsed)
            if self.delay > 0:
                time.sleep(self.delay)
            else:
                time.sleep(0.001)

class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.total = 0
        self.ok = 0
        self.err = 0
        self.total_time = 0.0
        self.last_errors = deque(maxlen=10)
        self.start_time = time.time()

    def add_result(self, success, status_code, elapsed):
        with self.lock:
            self.total += 1
            if success:
                self.ok += 1
            else:
                self.err += 1
                self.last_errors.append((status_code, datetime.now().strftime("%H:%M:%S")))
            self.total_time += elapsed

    def get_stats(self):
        with self.lock:
            total = self.total
            ok = self.ok
            err = self.err
            avg = self.total_time / total if total > 0 else 0
            rate = total / (time.time() - self.start_time) if (time.time() - self.start_time) > 0 else 0
            errors = list(self.last_errors)
        return total, ok, err, avg, rate, errors

def main():
    sys.stdout.write('\033[32m')

    parser = argparse.ArgumentParser(description=f"{NAME} - simple load testing tool")
    parser.add_argument("url", nargs="?", help="Target URL or IP address")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads")
    parser.add_argument("-d", "--delay", type=float, help="Delay between requests (seconds)")
    parser.add_argument("-r", "--report-interval", type=int, help="Statistics report interval (seconds)")
    args = parser.parse_args()

    if not args.url:
        print(f"=== {NAME} (light mode) ===\n")
        url = input("Enter target URL or IP address: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            sys.stdout.write('\033[0m')
            sys.exit(1)
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        try:
            threads = int(input("Number of threads (default 10): ").strip() or "10")
        except ValueError:
            threads = 10

        try:
            delay = float(input("Delay between requests (seconds, default 0.1): ").strip() or "0.1")
        except ValueError:
            delay = 0.1

        try:
            report_interval = int(input("Statistics report interval (seconds, default 2): ").strip() or "2")
        except ValueError:
            report_interval = 2
    else:
        url = args.url
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        threads = args.threads if args.threads is not None else 10
        delay = args.delay if args.delay is not None else 0.1
        report_interval = args.report_interval if args.report_interval is not None else 2

    print(f"\n=== {NAME} v{VERSION} ===")
    print(f"Target URL: {url}")
    print(f"Threads: {threads}, delay: {delay}s, report interval: {report_interval}s")

    ip, country = get_ip_info()
    print(f"Your IP: {ip}, Country: {country}\n")
    print("Press Ctrl+C to stop.\n")

    stats = Stats()
    stop_event = threading.Event()
    workers = []

    for i in range(threads):
        w = RequestWorker(url, delay, stats, stop_event, i+1)
        w.start()
        workers.append(w)

    art = r"""
    █   █  ███  █   █ █   █ █████ ████  ████  █   █ 
█   █ █   █ ██ ██ ██ ██ █     █   █ █   █  █ █  
█████ █████ █ █ █ █ █ █ ████  ████  ████    █   
█   █ █   █ █   █ █   █ █     █  █  █       █   
█   █ █   █ █   █ █   █ █████ █   █ █       █
    """
    sys.stdout.write('\033[37m')
    print(art)
    sys.stdout.write('\033[32m')

    print("\nrepo https://github.com/Harlabr/HammerPy/upload/main\n")

    try:
        while True:
            time.sleep(report_interval)
            total, ok, err, avg, rate, errors = stats.get_stats()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Requests: {total}, Success: {ok}, Errors: {err}, "
                  f"Avg time: {avg:.3f}s, RPS: {rate:.1f}")
            if errors:
                print("  Recent errors:")
                for code, tm in errors:
                    print(f"    {tm} - {code}")
    except KeyboardInterrupt:
        print("\nStopping by Ctrl+C...")
    finally:
        stop_event.set()
        for w in workers:
            w.stop()
        for w in workers:
            try:
                if w.thread.is_alive():
                    w.thread.join(timeout=0.5)
            except KeyboardInterrupt:
                print("Second interrupt - exiting immediately.")
                break
        print("Finished.")
        sys.stdout.write('\033[0m')

if __name__ == "__main__":
    main()
