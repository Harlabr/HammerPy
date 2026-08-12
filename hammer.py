#!/usr/bin/env python3

import sys
import time
import threading
import argparse
import requests
import json
import os
from datetime import datetime
from collections import deque

VERSION = "1.0"
NAME = "HammerPy"
CONFIG_FILE = "hammerpy_config.json"

TRANSLATIONS = {
    "en": {
        "welcome_light": "=== {} (light mode) ===\n",
        "enter_url": "Enter target URL or IP address: ",
        "no_url": "No URL provided. Exiting.",
        "threads_prompt": "Number of threads (default 10): ",
        "delay_prompt": "Delay between requests (seconds, default 0.1): ",
        "report_prompt": "Statistics report interval (seconds, default 2): ",
        "header": "=== {} v{} ===",
        "target": "Target URL: {}",
        "threads_delay": "Threads: {}, delay: {}s, report interval: {}s",
        "your_ip": "Your IP: {}, Country: {}",
        "press_ctrl": "Press Ctrl+C to stop.\n",
        "stats_line": "[{}] Requests: {}, Success: {}, Errors: {}, Avg time: {:.3f}s, RPS: {:.1f}",
        "recent_errors": "  Recent errors:",
        "error_item": "    {} - {}",
        "stopping": "\nStopping by Ctrl+C...",
        "finished": "Finished.",
        "second_interrupt": "Second interrupt - exiting immediately.",
        "choose_lang": "Choose language / Выберите язык:\n1. English\n2. Русский\nEnter 1 or 2: ",
    },
    "ru": {
        "welcome_light": "=== {} (легкий режим) ===\n",
        "enter_url": "Введите URL или IP-адрес сайта: ",
        "no_url": "URL не указан. Завершение.",
        "threads_prompt": "Количество потоков (по умолчанию 10): ",
        "delay_prompt": "Задержка между запросами (сек, по умолчанию 0.1): ",
        "report_prompt": "Интервал вывода статистики (сек, по умолчанию 2): ",
        "header": "=== {} v{} ===",
        "target": "Целевой URL: {}",
        "threads_delay": "Потоков: {}, задержка: {}с, интервал отчета: {}с",
        "your_ip": "Ваш IP: {}, Страна: {}",
        "press_ctrl": "Нажмите Ctrl+C для остановки.\n",
        "stats_line": "[{}] Запросов: {}, Успешно: {}, Ошибок: {}, Ср. время: {:.3f}с, RPS: {:.1f}",
        "recent_errors": "  Последние ошибки:",
        "error_item": "    {} - {}",
        "stopping": "\nОстановка по Ctrl+C...",
        "finished": "Завершено.",
        "second_interrupt": "Повторное прерывание – выходим немедленно.",
        "choose_lang": "Choose language / Выберите язык:\n1. English\n2. Русский\nВведите 1 или 2: ",
    }
}

def load_language():
    lang = "en"
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if "language" in data and data["language"] in ("en", "ru"):
                    lang = data["language"]
    except:
        pass
    return lang

def save_language(lang):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"language": lang}, f)
    except:
        pass

def get_text(key, lang, **kwargs):
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text

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
    lang = load_language()

    parser = argparse.ArgumentParser(description=f"{NAME} - load testing tool")
    parser.add_argument("url", nargs="?", help="Target URL or IP address")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads")
    parser.add_argument("-d", "--delay", type=float, help="Delay between requests (seconds)")
    parser.add_argument("-r", "--report-interval", type=int, help="Statistics report interval (seconds)")
    parser.add_argument("--lang", choices=["en", "ru"], help="Override language (en/ru)")
    args = parser.parse_args()

    if args.lang:
        lang = args.lang
        save_language(lang)

    if not os.path.exists(CONFIG_FILE) and not args.lang:
        sys.stdout.write(get_text("choose_lang", lang))
        choice = sys.stdin.readline().strip()
        if choice == "2":
            lang = "ru"
        else:
            lang = "en"
        save_language(lang)

    sys.stdout.write('\033[32m')

    if not args.url:
        print(get_text("welcome_light", lang, NAME))
        url = input(get_text("enter_url", lang)).strip()
        if not url:
            print(get_text("no_url", lang))
            sys.stdout.write('\033[0m')
            sys.exit(1)
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        try:
            threads = int(input(get_text("threads_prompt", lang)).strip() or "10")
        except ValueError:
            threads = 10

        try:
            delay = float(input(get_text("delay_prompt", lang)).strip() or "0.1")
        except ValueError:
            delay = 0.1

        try:
            report_interval = int(input(get_text("report_prompt", lang)).strip() or "2")
        except ValueError:
            report_interval = 2
    else:
        url = args.url
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        threads = args.threads if args.threads is not None else 10
        delay = args.delay if args.delay is not None else 0.1
        report_interval = args.report_interval if args.report_interval is not None else 2

    print(get_text("header", lang, NAME, VERSION))
    print(get_text("target", lang, url))
    print(get_text("threads_delay", lang, threads, delay, report_interval))

    ip, country = get_ip_info()
    print(get_text("your_ip", lang, ip, country))
    print(get_text("press_ctrl", lang))

    stats = Stats()
    stop_event = threading.Event()
    workers = []

    for i in range(threads):
        w = RequestWorker(url, delay, stats, stop_event, i+1)
        w.start()
        workers.append(w)

    art = r"""
█   █  ███  █   █ █   █ █████ ████  
█   █ █   █ ██ ██ ██ ██ █     █   █ 
█████ █████ █ █ █ █ █ █ ████  ████  
█   █ █   █ █   █ █   █ █     █  █  
█   █ █   █ █   █ █   █ █████ █   █
    """
    sys.stdout.write('\033[37m')
    print(art)
    sys.stdout.write('\033[32m')

    try:
        while True:
            time.sleep(report_interval)
            total, ok, err, avg, rate, errors = stats.get_stats()
            print(get_text("stats_line", lang,
                           datetime.now().strftime('%H:%M:%S'), total, ok, err, avg, rate))
            if errors:
                print(get_text("recent_errors", lang))
                for code, tm in errors:
                    print(get_text("error_item", lang, tm, code))
    except KeyboardInterrupt:
        print(get_text("stopping", lang))
    finally:
        stop_event.set()
        for w in workers:
            w.stop()
        for w in workers:
            try:
                if w.thread.is_alive():
                    w.thread.join(timeout=0.5)
            except KeyboardInterrupt:
                print(get_text("second_interrupt", lang))
                break
        print(get_text("finished", lang))
        sys.stdout.write('\033[0m')

if __name__ == "__main__":
    main()
