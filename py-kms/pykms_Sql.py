#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite database operations with transaction atomicity."""

import os
import logging
from typing import Optional, Dict, Any

# sqlite3 is optional.
try:
    import sqlite3
except ImportError:
    sqlite3 = None

from pykms_Format import pretty_printer

# --------------------------------------------------------------------------------------------------------------------------------------------------------

loggersrv = logging.getLogger("logsrv")


def sql_initialize(db_path: Optional[str] = None) -> str:
    """
    Initialize SQLite DB for client requests.

    Args:
            db_path: path to DB file (default 'clients.db')

    Returns:
            str: Path to database file

    Raises:
            sqlite3.Error: If database creation fails
    """
    if sqlite3 is None:
        raise ImportError("sqlite3 module not available")

    dbName = db_path if db_path is not None else "clients.db"
    if not os.path.isfile(dbName):
        # Initialize the database.
        con = None
        try:
            con = sqlite3.connect(dbName)
            con.isolation_level = "DEFERRED"  # Enable transaction support
            cur = con.cursor()
            cur.execute("""CREATE TABLE clients(
				clientMachineId TEXT PRIMARY KEY,
				machineName TEXT NOT NULL,
				applicationId TEXT NOT NULL,
				skuId TEXT NOT NULL,
				licenseStatus TEXT NOT NULL,
				lastRequestTime INTEGER NOT NULL,
				kmsEpid TEXT,
				requestCount INTEGER DEFAULT 1,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)""")
            con.commit()

        except sqlite3.Error as e:
            if con:
                con.rollback()
            pretty_printer(
                log_obj=loggersrv.error,
                to_exit=True,
                put_text="{reverse}{red}{bold}Database initialization failed: %s. Exiting...{end}" % str(e),
            )
        finally:
            if con:
                con.close()
    return dbName


def sql_update(dbName: str, infoDict: Dict[str, Any]) -> None:
    """
    Update or insert client record in database with atomic transaction.

    Args:
        dbName: Path to database file
        infoDict: Dictionary with client info

    Raises:
        sqlite3.Error: If database operation fails
    """
    if sqlite3 is None:
        loggersrv.warning("sqlite3 not available, skipping database update")
        return

    con = None
    try:
        con = sqlite3.connect(dbName)
        con.isolation_level = "DEFERRED"  # Start transaction
        cur = con.cursor()

        # Query existing record
        cur.execute("SELECT * FROM clients WHERE clientMachineId=?;", [infoDict["clientMachineId"]])
        data = cur.fetchone()

        if not data:
            # Insert new record
            cur.execute(
                """INSERT INTO clients 
                   (clientMachineId, machineName, applicationId, skuId, licenseStatus, lastRequestTime, requestCount) 
                   VALUES (?, ?, ?, ?, ?, ?, 1);""",
                (
                    infoDict["clientMachineId"],
                    infoDict["machineName"],
                    infoDict["appId"],
                    infoDict["skuId"],
                    infoDict["licenseStatus"],
                    infoDict["requestTime"],
                ),
            )
        else:
            # Update existing record - use single atomic UPDATE
            updates = []
            params = []

            if data[1] != infoDict["machineName"]:
                updates.append("machineName=?")
                params.append(infoDict["machineName"])

            if data[2] != infoDict["appId"]:
                updates.append("applicationId=?")
                params.append(infoDict["appId"])

            if data[3] != infoDict["skuId"]:
                updates.append("skuId=?")
                params.append(infoDict["skuId"])

            if data[4] != infoDict["licenseStatus"]:
                updates.append("licenseStatus=?")
                params.append(infoDict["licenseStatus"])

            if data[5] != infoDict["requestTime"]:
                updates.append("lastRequestTime=?")
                params.append(infoDict["requestTime"])

            # Always increment requestCount
            updates.append("requestCount=requestCount+1")
            updates.append("updated_at=CURRENT_TIMESTAMP")

            if updates:
                query = "UPDATE clients SET " + ", ".join(updates) + " WHERE clientMachineId=?;"
                params.append(infoDict["clientMachineId"])
                cur.execute(query, params)

        con.commit()

    except sqlite3.Error as e:
        if con:
            con.rollback()
        pretty_printer(
            log_obj=loggersrv.error,
            to_exit=True,
            put_text="{reverse}{red}{bold}Database update failed: %s. Exiting...{end}" % str(e),
        )
    finally:
        if con:
            con.close()


def sql_update_epid(dbName: str, kmsRequest: Any, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update ePID in database with atomic transaction.

    Args:
        dbName: Path to database file
        kmsRequest: KMS request object
        response: KMS response dictionary

    Returns:
        Dict[str, Any]: Updated response dictionary

    Raises:
        sqlite3.Error: If database operation fails
    """
    if sqlite3 is None:
        loggersrv.warning("sqlite3 not available, skipping ePID update")
        return response

    cmid = str(kmsRequest["clientMachineId"].get())
    con = None
    try:
        con = sqlite3.connect(dbName)
        con.isolation_level = "DEFERRED"  # Start transaction
        cur = con.cursor()

        # Get existing ePID
        cur.execute("SELECT kmsEpid FROM clients WHERE clientMachineId=?;", [cmid])
        data = cur.fetchone()

        if data and data[0]:
            # Use cached ePID from database
            response["kmsEpid"] = data[0].encode("utf-16le")
        else:
            # Store new ePID
            epid_str = response["kmsEpid"].decode("utf-16le")
            cur.execute(
                "UPDATE clients SET kmsEpid=?, updated_at=CURRENT_TIMESTAMP WHERE clientMachineId=?;", (epid_str, cmid)
            )

        con.commit()

    except sqlite3.Error as e:
        if con:
            con.rollback()
        pretty_printer(
            log_obj=loggersrv.error,
            to_exit=True,
            put_text="{reverse}{red}{bold}Database ePID update failed: %s. Exiting...{end}" % str(e),
        )
    finally:
        if con:
            con.close()

    return response
