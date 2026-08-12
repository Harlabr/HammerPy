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

    parser = argparse.ArgumentParser(description=f"{NAME} – простой нагрузочный инструмент")
    parser.add_argument("url", nargs="?", help="URL или IP-адрес")
    parser.add_argument("-t", "--threads", type=int, help="Количество потоков")
    parser.add_argument("-d", "--delay", type=float, help="Задержка между запросами (сек)")
    parser.add_argument("-r", "--report-interval", type=int, help="Интервал вывода статистики (сек)")
    args = parser.parse_args()

    if not args.url:
        print(f"=== {NAME} (легкий режим) ===\n")
        url = input("Введите URL или IP-адрес сайта: ").strip()
        if not url:
            print("URL не указан. Завершение.")
            sys.stdout.write('\033[0m')
            sys.exit(1)
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        try:
            threads = int(input("Количество потоков (по умолчанию 10): ").strip() or "10")
        except ValueError:
            threads = 10

        try:
            delay = float(input("Задержка между запросами (сек, по умолчанию 0.1): ").strip() or "0.1")
        except ValueError:
            delay = 0.1

        try:
            report_interval = int(input("Интервал вывода статистики (сек, по умолчанию 2): ").strip() or "2")
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
    print(f"Целевой URL: {url}")
    print(f"Потоков: {threads}, задержка: {delay} с, интервал отчёта: {report_interval} с")

    ip, country = get_ip_info()
    print(f"Ваш IP: {ip}, Страна: {country}\n")
    print("Нажмите Ctrl+C для остановки.\n")

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
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Запросов: {total}, Успешно: {ok}, Ошибок: {err}, "
                  f"Ср. время: {avg:.3f} с, RPS: {rate:.1f}")
            if errors:
                print("  Последние ошибки:")
                for code, tm in errors:
                    print(f"    {tm} - {code}")
    except KeyboardInterrupt:
        print("\nОстановка по Ctrl+C...")
    finally:
        stop_event.set()
        for w in workers:
            w.stop()
        for w in workers:
            try:
                if w.thread.is_alive():
                    w.thread.join(timeout=0.5)
            except KeyboardInterrupt:
                print("Повторное прерывание – выходим немедленно.")
                break
        print("Завершено.")
        sys.stdout.write('\033[0m')

if __name__ == "__main__":
    main()