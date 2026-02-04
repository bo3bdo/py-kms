#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Socket helpers: dual-stack IPv6 and MultipleListener (from Py-KMS-Organization)."""

import os
import socket
import selectors
import ipaddress
import logging
from pykms_Format import pretty_printer

loggersrv = logging.getLogger('logsrv')


def has_dualstack_ipv6():
        """Return True if the platform supports creating a SOCK_STREAM socket
        which can handle both AF_INET and AF_INET6 (IPv4 / IPv6) connections.
        """
        if not socket.has_ipv6:
                return False
        try:
                with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
                        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                return True
        except (socket.error, OSError):
                return False


def create_server_sock(address, *, family=socket.AF_INET, backlog=None, reuse_port=False, dualstack_ipv6=False):
        """Create a SOCK_STREAM socket bound to *address* (host, port).
        *family*: AF_INET or AF_INET6.
        *backlog*: passed to socket.listen().
        *reuse_port*: use SO_REUSEPORT if supported.
        *dualstack_ipv6*: if True and family is AF_INET6, set IPV6_V6ONLY=0 to accept IPv4 and IPv6.
        """
        if reuse_port and not getattr(socket, "SO_REUSEPORT", None):
                pretty_printer(log_obj=loggersrv.warning, put_text="{reverse}{yellow}{bold}SO_REUSEPORT not supported on this platform - ignoring socket option.{end}")
                reuse_port = False

        if dualstack_ipv6:
                if not has_dualstack_ipv6():
                        raise ValueError("dualstack_ipv6 not supported on this platform")
                if family != socket.AF_INET6:
                        raise ValueError("dualstack_ipv6 requires AF_INET6 family")

        sock = socket.socket(family, socket.SOCK_STREAM)
        try:
                if os.name not in ('nt', 'cygwin') and hasattr(socket, 'SO_REUSEADDR'):
                        try:
                                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        except socket.error:
                                pass
                if reuse_port:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                if socket.has_ipv6 and family == socket.AF_INET6:
                        if dualstack_ipv6:
                                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                        elif hasattr(socket, 'IPV6_V6ONLY'):
                                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                sock.bind(address)
                if backlog is None:
                        sock.listen()
                else:
                        sock.listen(backlog)
                return sock
        except (socket.error, OSError):
                sock.close()
                raise


class MultipleListener(object):
        """Listen on multiple addresses as (host, port, backlog, reuse_port) tuples.
        Useful when dual-stack is not supported (e.g. Windows): listen on both 0.0.0.0 and ::.
        """
        def __init__(self, addresses=None, want_dual=False):
                self.socks = []
                self.sockmap = {}
                addresses = addresses or []
                completed = False
                try:
                        for addr in addresses:
                                addr = self._check(addr)
                                ip_ver = ipaddress.ip_address(addr[0])
                                sock = create_server_sock(
                                        (addr[0], addr[1]),
                                        family=(socket.AF_INET if ip_ver.version == 4 else socket.AF_INET6),
                                        backlog=addr[2],
                                        reuse_port=addr[3],
                                        dualstack_ipv6=(False if ip_ver.version == 4 else want_dual)
                                )
                                self.socks.append(sock)
                                self.sockmap[sock.fileno()] = sock
                        completed = True
                finally:
                        if not completed:
                                self.close()

        def _check(self, address):
                if len(address) < 2:
                        raise socket.error("missing host or port")
                if len(address) == 2:
                        address = address + (None, True)
                elif len(address) == 3:
                        address = address + (True,)
                return address

        def filenos(self):
                return list(self.sockmap.keys())

        def register(self, pollster):
                for fd in self.filenos():
                        pollster.register(fileobj=fd, events=selectors.EVENT_READ)

        def accept(self):
                """Accept from first ready socket (blocking)."""
                with selectors.DefaultSelector() as sel:
                        self.register(sel)
                        events = sel.select()
                        if not events:
                                return None, None
                        fd = events[0][0].fd
                        return self.sockmap[fd].accept()

        def close(self):
                for sock in self.socks:
                        try:
                                sock.close()
                        except socket.error:
                                pass
                self.socks = []
                self.sockmap = {}

        def getsockname(self):
                if self.socks:
                        return self.socks[0].getsockname()
                return ()

        def settimeout(self, timeout):
                for sock in self.socks:
                        sock.settimeout(timeout)

        def gettimeout(self):
                return self.socks[0].gettimeout() if self.socks else None
