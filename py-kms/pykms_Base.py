#!/usr/bin/env python3
"""KMS request/response logic and base structures."""

from __future__ import annotations

import binascii
import logging
import time
import uuid
import socket

from pykms_Structure import Structure
from pykms_DB2Dict import kmsDB2Dict
from pykms_PidGenerator import epidGenerator
from pykms_Filetimes import filetime_to_dt
from pykms_Sql import sql_initialize, sql_update, sql_update_epid
from pykms_Format import justify, byterize, enco, deco, pretty_printer

# --------------------------------------------------------------------------------------------------------------------------------------------------------

loggersrv = logging.getLogger("logsrv")


class UUID(Structure):
    commonHdr = ()
    structure = (("raw", "16s"),)

    def get(self):
        return uuid.UUID(bytes_le=enco(str(self), "latin-1"))


class kmsBase:
    """Base for KMS request handling; holds request/response structures and server logic."""

    def __init__(self, data: bytes | None, srv_config: dict) -> None:
        self.data = data
        self.srv_config = srv_config

    class kmsRequestStruct(Structure):
        commonHdr = ()
        structure = (
            ("versionMinor", "<H"),
            ("versionMajor", "<H"),
            ("isClientVm", "<I"),
            ("licenseStatus", "<I"),
            ("graceTime", "<I"),
            ("applicationId", ":", UUID),
            ("skuId", ":", UUID),
            ("kmsCountedId", ":", UUID),
            ("clientMachineId", ":", UUID),
            ("requiredClientCount", "<I"),
            ("requestTime", "<Q"),
            ("previousClientMachineId", ":", UUID),
            ("machineName", "u"),
            ("_mnPad", "_-mnPad", "126-len(machineName)"),
            ("mnPad", ":"),
        )

        def getMachineName(self):
            return self["machineName"].decode("utf-16le")

        def getLicenseStatus(self):
            return kmsBase.licenseStates[self["licenseStatus"]] or "Unknown"

    class kmsResponseStruct(Structure):
        commonHdr = ()
        structure = (
            ("versionMinor", "<H"),
            ("versionMajor", "<H"),
            ("epidLen", "<I=len(kmsEpid)+2"),
            ("kmsEpid", "u"),
            ("clientMachineId", ":", UUID),
            ("responseTime", "<Q"),
            ("currentClientCount", "<I"),
            ("vLActivationInterval", "<I"),
            ("vLRenewalInterval", "<I"),
        )

    class GenericRequestHeader(Structure):
        commonHdr = ()
        structure = (
            ("bodyLength1", "<I"),
            ("bodyLength2", "<I"),
            ("versionMinor", "<H"),
            ("versionMajor", "<H"),
            ("remainder", "_"),
        )

    licenseStates = {
        0: "Unlicensed",
        1: "Activated",
        2: "Grace Period",
        3: "Out-of-Tolerance Grace Period",
        4: "Non-Genuine Grace Period",
        5: "Notifications Mode",
        6: "Extended Grace Period",
    }

    licenseStatesEnum = {
        "unlicensed": 0,
        "licensed": 1,
        "oobGrace": 2,
        "ootGrace": 3,
        "nonGenuineGrace": 4,
        "notification": 5,
        "extendedGrace": 6,
    }

    def getPadding(self, bodyLength):
        ## https://forums.mydigitallife.info/threads/71213-Source-C-KMS-Server-from-Microsoft-Toolkit?p=1277542&viewfull=1#post1277542
        return 4 + (((~bodyLength & 3) + 1) & 3)

    def serverLogic(self, kmsRequest):
        if self.srv_config["sqlite"] and self.srv_config["dbSupport"]:
            self.dbName = sql_initialize(self.srv_config.get("sqlitedb", "clients.db"))

        pretty_printer(num_text=15, where="srv")
        kmsRequest = byterize(kmsRequest)
        loggersrv.debug(
            "KMS Request Bytes: \n%s\n" % justify(deco(binascii.b2a_hex(enco(str(kmsRequest), "latin-1")), "latin-1"))
        )
        loggersrv.debug("KMS Request: \n%s\n" % justify(kmsRequest.dump(print_to_stdout=False)))

        clientMachineId = kmsRequest["clientMachineId"].get()
        applicationId = kmsRequest["applicationId"].get()
        skuId = kmsRequest["skuId"].get()
        requestDatetime = filetime_to_dt(kmsRequest["requestTime"])

        # Localize the request time, if module "tzlocal" is available.
        local_dt = requestDatetime
        try:
            from tzlocal import get_localzone

            try:
                tz = get_localzone()
                # Handle both pytz and zoneinfo.ZoneInfo objects
                if hasattr(tz, "localize"):
                    # pytz timezone (has localize method)
                    local_dt = tz.localize(requestDatetime)
                else:
                    # zoneinfo.ZoneInfo (Python 3.9+, use replace method)
                    local_dt = requestDatetime.replace(tzinfo=tz)
            except Exception as e:
                loggersrv.debug(f"Could not localize timezone: {e}")
                local_dt = requestDatetime
        except ImportError:
            loggersrv.debug("tzlocal module not available, using naive datetime")

        # Activation threshold.
        # https://docs.microsoft.com/en-us/windows/deployment/volume-activation/activate-windows-10-clients-vamt
        MinClients = kmsRequest["requiredClientCount"]
        RequiredClients = MinClients * 2
        if self.srv_config["clientcount"] != None:
            if 0 < self.srv_config["clientcount"] < MinClients:
                # fixed to 6 (product server) or 26 (product desktop)
                currentClientCount = MinClients + 1
                pretty_printer(
                    log_obj=loggersrv.warning,
                    put_text="{reverse}{yellow}{bold}Not enough clients ! Fixed with %s, but activated client \
could be detected as not genuine !{end}"
                    % currentClientCount,
                )
            elif MinClients <= self.srv_config["clientcount"] < RequiredClients:
                currentClientCount = self.srv_config["clientcount"]
                pretty_printer(
                    log_obj=loggersrv.warning,
                    put_text="{reverse}{yellow}{bold}With count = %s, activated client could be detected as not genuine !{end}"
                    % currentClientCount,
                )
            elif self.srv_config["clientcount"] >= RequiredClients:
                # fixed to 10 (product server) or 50 (product desktop)
                currentClientCount = RequiredClients
                if self.srv_config["clientcount"] > RequiredClients:
                    pretty_printer(
                        log_obj=loggersrv.warning,
                        put_text="{reverse}{yellow}{bold}Too many clients ! Fixed with %s{end}" % currentClientCount,
                    )
        else:
            # fixed to 10 (product server) or 50 (product desktop)
            currentClientCount = RequiredClients

        # Get a name for SkuId, AppId.
        kmsdb = kmsDB2Dict()
        skuName = None
        appName = None

        appitems = kmsdb[2]
        for appitem in appitems:
            try:
                if uuid.UUID(appitem["Id"]) == applicationId:
                    appName = appitem["DisplayName"]
                    break
            except (ValueError, KeyError, TypeError):
                # Skip invalid UUID or missing fields
                continue

            # Also search for SKU within this app
            try:
                kmsitems = appitem.get("KmsItems", [])
                for kmsitem in kmsitems:
                    skuitems = kmsitem.get("SkuItems", [])
                    for skuitem in skuitems:
                        try:
                            if uuid.UUID(skuitem["Id"]) == skuId:
                                skuName = skuitem["DisplayName"]
                                break
                        except (ValueError, KeyError, TypeError):
                            # Skip invalid SKU entries
                            continue
                    if skuName:
                        break
            except (KeyError, TypeError):
                # Skip apps with invalid structure
                continue

        # Set defaults if not found
        if not skuName:
            skuName = str(skuId)
            loggersrv.warning("Unknown SKU ID: %s" % skuId)

        if not appName:
            appName = str(applicationId)
            loggersrv.warning("Unknown Application ID: %s" % applicationId)

        infoDict = {
            "machineName": kmsRequest.getMachineName(),
            "clientMachineId": str(clientMachineId),
            "appId": appName,
            "skuId": skuName,
            "licenseStatus": kmsRequest.getLicenseStatus(),
            "requestTime": int(time.time()),
            "kmsEpid": None,
        }

        loggersrv.info("Machine Name: %s" % infoDict["machineName"])
        loggersrv.info("Client Machine ID: %s" % infoDict["clientMachineId"])
        loggersrv.info("Application ID: %s" % infoDict["appId"])
        loggersrv.info("SKU ID: %s" % infoDict["skuId"])
        loggersrv.info("License Status: %s" % infoDict["licenseStatus"])
        loggersrv.info("Request Time: %s" % local_dt.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)"))

        if self.srv_config["loglevel"] == "MINI":
            loggersrv.mini(
                "",
                extra={
                    "host": socket.gethostname() + " [" + self.srv_config["ip"] + "]",
                    "status": infoDict["licenseStatus"],
                    "product": infoDict["skuId"],
                },
            )

        if self.srv_config["sqlite"] and self.srv_config["dbSupport"]:
            sql_update(self.dbName, infoDict)

        return self.createKmsResponse(kmsRequest, currentClientCount)

    def createKmsResponse(self, kmsRequest, currentClientCount):
        response = self.kmsResponseStruct()
        response["versionMinor"] = kmsRequest["versionMinor"]
        response["versionMajor"] = kmsRequest["versionMajor"]

        if not self.srv_config["epid"]:
            response["kmsEpid"] = epidGenerator(
                kmsRequest["kmsCountedId"].get(), kmsRequest["versionMajor"], self.srv_config["lcid"]
            ).encode("utf-16le")
        else:
            response["kmsEpid"] = self.srv_config["epid"].encode("utf-16le")

        response["clientMachineId"] = kmsRequest["clientMachineId"]
        # rule: timeserver - 4h <= timeclient <= timeserver + 4h, check if is satisfied.
        response["responseTime"] = kmsRequest["requestTime"]
        response["currentClientCount"] = currentClientCount
        response["vLActivationInterval"] = self.srv_config["activation"]
        response["vLRenewalInterval"] = self.srv_config["renewal"]

        if self.srv_config["sqlite"] and self.srv_config["dbSupport"]:
            response = sql_update_epid(self.dbName, kmsRequest, response)

        loggersrv.info("Server ePID: %s" % response["kmsEpid"].decode("utf-16le"))

        return response


import pykms_RequestV4, pykms_RequestV5, pykms_RequestV6, pykms_RequestUnknown


def generateKmsResponseData(data: bytes, srv_config: dict) -> bytes:
    """Build KMS response bytes from request data and server config. Dispatches by protocol version (V4/V5/V6)."""
    version = kmsBase.GenericRequestHeader(data)["versionMajor"]
    currentDate = time.strftime("%a %b %d %H:%M:%S %Y")

    if version == 4:
        loggersrv.info("Received V%d request on %s." % (version, currentDate))
        messagehandler = pykms_RequestV4.kmsRequestV4(data, srv_config)
    elif version == 5:
        loggersrv.info("Received V%d request on %s." % (version, currentDate))
        messagehandler = pykms_RequestV5.kmsRequestV5(data, srv_config)
    elif version == 6:
        loggersrv.info("Received V%d request on %s." % (version, currentDate))
        messagehandler = pykms_RequestV6.kmsRequestV6(data, srv_config)
    else:
        loggersrv.info("Unhandled KMS version V%d." % version)
        messagehandler = pykms_RequestUnknown.kmsRequestUnknown(data, srv_config)

    return messagehandler.executeRequestLogic()
