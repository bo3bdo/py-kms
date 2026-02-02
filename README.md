# py-kms

**KMS Server Emulator** written in Python — activates Windows and Office volume licenses.

[![License](https://img.shields.io/badge/license-unlicense-lightgray.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

---

## History

_py-kms_ is a port of [node-kms](http://forums.mydigitallife.info/members/183074-markedsword) (by cyrozap), which is a port of the C# / C++ / .NET KMS Emulator. The original implementation was written by [CODYQX4](http://forums.mydigitallife.info/members/89933-CODYQX4) and is derived from reverse‑engineered code of Microsoft’s official KMS.

---

## Features

- Responds to **V4, V5, and V6** KMS requests.
- **Supported products:**
  - **Windows:** Vista, 7, 8, 8.1, 10, **11**
  - **Windows Server:** 2008, 2008 R2, 2012, 2012 R2, 2016, 2019, **2022**, **2024**, **2025**
  - **Office (Volume):** 2010, 2013, 2016, 2019, **2021**, **2024**
- Written in **Python 3** (tested with Python 3.8–3.12).
- Compatible with **Windows** (including Python 3.10+ `select` fixes) and **Unix**.

---

## Dependencies

- **Python 3.8+**
- **Tkinter** (for GUI)
- Optional: **tzlocal** — converts “Request Time” to local time in verbose output (otherwise UTC).
- Optional: **sqlite3** — for database support (store activation data).

**Example (Ubuntu / Debian):**
```bash
sudo apt-get update
sudo apt-get install python3-tk python3-pip
sudo pip3 install tzlocal
```

---

## Quick Start

**Server (default: all interfaces, port 1688):**
```bash
python3 pykms_Server.py
# Or: python3 pykms_Server.py 0.0.0.0 1688
```

**Client (test only):**
```bash
python3 pykms_Client.py 127.0.0.1 1688 -m Windows11 -V INFO
```

---

## Usage

| Action | Command |
|--------|--------|
| Start server | `python3 pykms_Server.py [IP] [PORT]` — default IP: `0.0.0.0` or `::`, port: `1688` |
| Run client | `python3 pykms_Client.py [IP] [PORT]` |
| Help | `python3 pykms_Server.py -h` and `python3 pykms_Client.py -h` |
| Random HWID | `python3 pykms_Server.py -w RANDOM` |
| Client example | `python3 pykms_Client.py 0.0.0.0 1688 -m Windows11 -V INFO` |

**Client mode (`-m`):**  
`WindowsVista`, `Windows7`, `Windows8`, `Windows8.1`, `Windows10`, `Windows11`, `WindowsServer2022`, `WindowsServer2024`, `WindowsServer2025`, `Office2010`, `Office2013`, `Office2016`, `Office2019`, `Office2021`, `Office2024`.

**Logging:**
- `-F /path/to/logfile.log -V DEBUG` — log to file, DEBUG level.
- `-F STDOUT -V DEBUG` — log to stdout.
- `-F FILESTDOUT /path/to/logfile.log` — file + stdout.
- `-V MINI` — minimal logging.

**Other:**
- `-t0 10` — idle timeout (seconds).
- `-y` — asynchronous (pretty) logging.
- **Etrigan (daemon):** `python3 pykms_Server.py etrigan start` / `etrigan stop`.
- **GUI with Etrigan:** `python3 pykms_Server.py etrigan start -g`.

---

## Docker

[![Docker](https://img.shields.io/docker/cloud/automated/pykmsorg/py-kms)](https://hub.docker.com/r/pykmsorg/py-kms)
[![Pulls](https://img.shields.io/docker/pulls/pykmsorg/py-kms)](https://hub.docker.com/r/pykmsorg/py-kms)

Images are in the `docker/` folder. Tags:

- **latest** / **minimal** — minimal image (no SQLite).
- **python3** — full image with SQLite and web interface.

Run from Docker Hub:
```bash
docker run -d -p 1688:1688 pykmsorg/py-kms
```

To keep images updated automatically, see [watchtower](https://github.com/containrrr/watchtower).

---

## More

- **Wiki:** [py-kms Wiki](https://github.com/SystemRage/py-kms/wiki) — activation notes and GVLK keys.
- **License:** [Unlicense](LICENSE) (py-kms); [MIT](LICENSE.gui.md) (GUI © Matteo ℱan).
