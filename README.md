# HammerPy 🔨

A simple and efficient stress‑testing tool written in Python, featuring multithreading, colored output, and a minimalistic ASCII logo.

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![GitHub stars](https://img.shields.io/github/stars/Harlabr/HammerPy.svg?style=social&label=Stars)](https://github.com/Harlabr/HammerPy)
[![GitHub forks](https://img.shields.io/github/forks/Harlabr/HammerPy.svg?style=social&label=Forks)](https://github.com/Harlabr/HammerPy)
[![GitHub watchers](https://img.shields.io/github/watchers/Harlabr/HammerPy.svg?style=social&label=Watchers)](https://github.com/Harlabr/HammerPy)

## 🚀 Features

- **Multithreading** – configurable number of parallel workers.
- **Adjustable delay** – set the interval between requests in seconds (floating point allowed).
- **Real‑time statistics** – total requests, successes, failures, average response time, and RPS (requests per second).
- **Last errors display** – shows the most recent 10 errors with timestamps and status codes/types.
- **Automatic IP & country detection** – using public APIs.
- **Colored terminal output** – main information in green, ASCII art in white.
- **Interactive mode** – if run without arguments, prompts for parameters.

## 📦 Installation

```bash
git clone https://github.com/Harlabr/HammerPy.git
cd HammerPy
pip install requests
```

## 🛠 Usage

### Command line

```bash
python hammera.py <URL> [-t THREADS] [-d DELAY] [-r REPORT_INTERVAL]
```

Example:
```bash
python hammera.py https://example.com -t 20 -d 0.05 -r 3
```

### Interactive mode

Just run without arguments and follow the prompts:
```bash
python hammera.py
```

## 📋 Arguments

| Argument              | Description                                 |
|-----------------------|---------------------------------------------|
| `url`                 | Target URL or IP address (http:// is optional) |
| `-t, --threads`       | Number of worker threads (default: 10)      |
| `-d, --delay`         | Delay between requests in seconds (default: 0.1) |
| `-r, --report-interval` | Statistics output interval in seconds (default: 2) |

## 📊 Example output

```
=== HammerPy v1.0 ===
Target URL: http://example.com
Threads: 10, delay: 0.1 s, report interval: 2 s
Your IP: 192.168.1.1, Country: Russia

Press Ctrl+C to stop.

█   █  ███  █   █ █   █ █████ ████  ████  █   █ 
█   █ █   █ ██ ██ ██ ██ █     █   █ █   █  █ █  
█████ █████ █ █ █ █ █ █ ████  ████  ████    █   
█   █ █   █ █   █ █   █ █     █  █  █       █   
█   █ █   █ █   █ █   █ █████ █   █ █       █

repo https://github.com/Harlabr/HammerPy

[14:32:15] Requests: 150, Success: 148, Errors: 2, Avg time: 0.234 s, RPS: 74.8
  Last errors:
    14:31:59 - 404
    14:32:01 - ConnectionError
```

## 📝 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Harlabr** – [GitHub](https://github.com/Harlabr)

---

![Mrrobot](https://media1.tenor.com/m/TdfVOIHjS6gAAAAC/shaking-mr-robot-mr-robot.gif)
