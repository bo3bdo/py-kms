# py-kms — Setup, Installation & Run Guide

Step-by-step guide to install and run the **KMS server** and **client** on Windows or Linux.

---

## 1. What you need

- **Python 3.8 or newer** — [python.org](https://www.python.org/downloads/)
- **Tkinter** — for the GUI (optional; usually included with Python)
- Optional: **tzlocal** (for local time in logs), **sqlite3** (for activation database)

---

## 2. Get the project

Clone or download the repository, then go into the **`py-kms`** folder (the one that contains `pykms_Server.py` and `pykms_Client.py`):

```bash
cd path/to/py-kms
cd py-kms
```

All commands below must be run from this **`py-kms`** folder.

---

## 3. Install dependencies (optional)

**Windows (if you use pip):**
```bash
pip install tzlocal
```

**Linux (e.g. Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3-tk python3-pip
pip3 install tzlocal
```

---

## 4. Run the server

From the **`py-kms`** folder:

**Listen on all interfaces (default port 1688):**
```bash
python pykms_Server.py
```

**Listen on a specific IP and port:**
```bash
python pykms_Server.py 0.0.0.0 1688
```

**Windows — listen on localhost only:**
```bash
python pykms_Server.py 127.0.0.1 1688
```

Leave this terminal open; the server runs until you press **Ctrl+C**.

---

## 5. Run the client (test from the same machine)

Open a **second terminal**, go to the **`py-kms`** folder, then run the client against the server.

**Default (server on localhost, port 1688):**
```bash
cd py-kms
python pykms_Client.py 127.0.0.1 1688 -m Windows11 -V INFO
```

**Other examples:**
```bash
# Windows Server 2025
python pykms_Client.py 127.0.0.1 1688 -m WindowsServer2025 -V INFO

# Windows 10
python pykms_Client.py 127.0.0.1 1688 -m Windows10 -V INFO

# Office 2021
python pykms_Client.py 127.0.0.1 1688 -m Office2021 -V INFO
```

**Client modes (`-m`):**  
`Windows11`, `Windows10`, `WindowsServer2022`, `WindowsServer2024`, `WindowsServer2025`, `Office2019`, `Office2021`, `Office2024`, etc.

If the server is running, you should see a success message in the client output.

---

## 6. Run the GUI (Windows)

On **Windows**, you can start the graphical interface from the **`py-kms`** folder:

```bash
cd py-kms
python pykms_Server.py etrigan start -g
```

The GUI opens; you can start/stop the server and open the client from the window.  
Close the window to exit.

---

## 7. Activate a real Windows machine

On the **Windows** PC you want to activate (same network as the machine running py-kms):

1. Open **Command Prompt as Administrator**.
2. Set the KMS server (replace `KMS_SERVER_IP` with the IP of the machine where py-kms runs):
   ```cmd
   slmgr /skms KMS_SERVER_IP:1688
   ```
3. Install the product key (example: Windows 11 Enterprise):
   ```cmd
   slmgr /ipk NPPR9-FWDCX-D2C8J-H872K-2YT43
   ```
4. Activate:
   ```cmd
   slmgr /ato
   ```
5. Check status:
   ```cmd
   slmgr /dlv
   ```

---

## 8. Quick reference

| Task              | Command |
|-------------------|--------|
| Start server      | `python pykms_Server.py [IP] [PORT]` |
| Run client        | `python pykms_Client.py 127.0.0.1 1688 -m Windows11 -V INFO` |
| Start GUI (Windows) | `python pykms_Server.py etrigan start -g` |
| Server help       | `python pykms_Server.py -h` |
| Client help       | `python pykms_Client.py -h` |

**Important:** Always run these commands from the **`py-kms`** folder.

For more options, GVLK keys, and Docker, see the main [README.md](README.md) and the [Wiki](https://github.com/SystemRage/py-kms/wiki).
