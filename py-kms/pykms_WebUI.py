#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple Web UI for py-kms: status page (no Flask)."""

import html
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
        from pykms_version import __version__ as _version
except ImportError:
        _version = "unknown"


def _escape(s):
        return html.escape(str(s), quote=True)


def _is_modern_edition(row):
        """True if product/edition is from 2020 or later (for table filter)."""
        s = " ".join([str(row.get("app", "")), str(row.get("kms", "")), str(row.get("sku", ""))]).lower()
        if "windows 11" in s or "windows 10 20" in s or "windows 10 21" in s:
                return True
        if "windows server 2022" in s or "windows server 2025" in s:
                return True
        if "office 2019" in s or "office 2021" in s or "office 2024" in s:
                return True
        if "ltsc 2021" in s or "ltsc 2024" in s:
                return True
        for y in ("2020", "2021", "2022", "2023", "2024", "2025"):
                if y in s:
                        return True
        return False


def _get_gvlk_list():
        """Return list of {app, kms, sku, gvlk} from KmsDataBase for products that have Gvlk."""
        out = []
        try:
                from pykms_DB2Dict import kmsDB2Dict
                kmsdb = kmsDB2Dict()
                appitems = kmsdb[2]
                for app in appitems:
                        app_name = app.get("DisplayName", "")
                        for kms in app.get("KmsItems", []):
                                kms_name = kms.get("DisplayName", "")
                                for sku in kms.get("SkuItems", []):
                                        gvlk = sku.get("Gvlk", "").strip()
                                        if not gvlk:
                                                continue
                                        sku_name = sku.get("DisplayName", "")
                                        row = {
                                                "app": app_name,
                                                "kms": kms_name,
                                                "sku": sku_name,
                                                "gvlk": gvlk,
                                        }
                                        if _is_modern_edition(row):
                                                out.append(row)
        except Exception:
                pass
        return out


def _build_status_html(srv_config):
        """Build minimal status HTML; srv_config can be None if server not ready."""
        ip = _escape(srv_config.get("ip", "0.0.0.0")) if srv_config else "—"
        port = srv_config.get("port", 1688) if srv_config else 1688
        kms_addr = "%s:%s" % (ip, port)
        title = "py-kms Status"
        body = [
                "<!DOCTYPE html><html><head><meta charset='utf-8'><title>%s</title>" % _escape(title),
                "<style>body{font-family:sans-serif;max-width:640px;margin:2em auto;padding:0 1em;}",
                "h1{color:#333;} code{background:#eee;padding:.2em .4em;} pre{background:#f5f5f5;padding:1em;overflow:auto;}</style></head><body>",
                "<h1>%s</h1>" % _escape(title),
                "<p><strong>Version:</strong> %s</p>" % _escape(_version),
                "<p><strong>Status:</strong> <span style='color:green'>Running</span></p>",
                "<p><strong>KMS address:</strong> <code>%s</code></p>" % _escape(kms_addr),
        ]
        if srv_config and srv_config.get("sqlite"):
                try:
                        from pykms_Sql import sql_get_all
                        db_path = srv_config.get("sqlitedb", "clients.db")
                        if os.path.isfile(db_path):
                                clients = sql_get_all(db_path)
                                count = len(clients) if clients else 0
                                body.append("<p><strong>Clients in database:</strong> %s</p>" % count)
                except Exception:
                        pass
        body.append("<h2>Activation (Windows)</h2>")
        body.append("<pre>slmgr /skms " + _escape(kms_addr) + "\nslmgr /ipk &lt;GVLK&gt;\nslmgr /ato\nslmgr /dlv</pre>")
        gvlk_list = _get_gvlk_list()
        if gvlk_list:
                body.append("<h2>GVLK keys (copy command)</h2>")
                body.append("<p>Modern editions only (2020–latest). Choose your edition and copy the command to run as Administrator:</p>")
                body.append("<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;max-width:800px;'>")
                body.append("<tr><th>Product</th><th>Edition</th><th>Command (slmgr /ipk)</th><th></th></tr>")
                for row in gvlk_list:
                        cmd = "slmgr /ipk " + row["gvlk"]
                        body.append("<tr><td>%s</td><td>%s</td><td><code class='gvlk-cmd'>%s</code></td><td><button type='button' class='copy-cmd' data-cmd='%s'>Copy</button></td></tr>"
                                % (_escape(row["app"]), _escape(row["sku"]), _escape(cmd), _escape(cmd)))
                body.append("</table>")
                body.append("<script>document.querySelectorAll('.copy-cmd').forEach(function(b){b.onclick=function(){var c=this.getAttribute('data-cmd');if(c){navigator.clipboard.writeText(c);this.textContent='Copied!';}};});</script>")
        body.append("<p><a href='https://github.com/SystemRage/py-kms/wiki'>Wiki (GVLK keys)</a></p>")
        body.append("</body></html>")
        return "\n".join(body).encode("utf-8")


class _StatusHandler(BaseHTTPRequestHandler):
        srv_config_ref = None  # set by server to current srv_config

        def do_GET(self):
                if self.path in ("/", "/status", "/index.html"):
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(_build_status_html(getattr(self, "srv_config_ref", None) or _StatusHandler.srv_config_ref))
                else:
                        self.send_response(404)
                        self.end_headers()

        def log_message(self, format, *args):
                pass  # quiet


class _ReuseHTTPServer(HTTPServer):
        allow_reuse_address = True


def start_webui_thread(port, srv_config, bind_ip="127.0.0.1"):
        """Start the status Web UI in a daemon thread on (bind_ip, port)."""
        _StatusHandler.srv_config_ref = srv_config
        server = _ReuseHTTPServer((bind_ip, port), _StatusHandler)
        thread = threading.Thread(target=server.serve_forever, name="WebUI", daemon=True)
        thread.start()
        return server, thread
