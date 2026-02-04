#!/usr/bin/env python3

import os
from datetime import datetime
import xml.etree.ElementTree as ET

#---------------------------------------------------------------------------------------------------------------------------------------------------------

def _normalize_winbuilds(winbuilds):
        """Support KmsData 2.0: add MinDate from ReleaseDate, assign WinBuildIndex for UseForEpid builds."""
        for wb in winbuilds:
                if wb.get('ReleaseDate') and not wb.get('MinDate'):
                        try:
                                s = wb['ReleaseDate'].replace('Z', '+00:00')
                                dt = datetime.fromisoformat(s)
                                wb['MinDate'] = dt.strftime('%d/%m/%Y')
                        except (ValueError, KeyError):
                                pass
                if wb.get('UseForEpid', '').lower() == 'true' and 'WinBuildIndex' not in wb:
                        pass  # set in next loop
        epid_idx = 0
        for wb in winbuilds:
                if wb.get('UseForEpid', '').lower() == 'true':
                        wb['WinBuildIndex'] = str(epid_idx)
                        epid_idx += 1
        return winbuilds

def kmsDB2Dict():
        path = os.path.join(os.path.dirname(__file__), 'KmsDataBase.xml')
        root = ET.parse(path).getroot()

        kmsdb, child1, child2, child3 = [ [] for _ in range(4) ]

        ## Get winbuilds.
        for winbuild in root.iter('WinBuild'):
                child1.append(winbuild.attrib)

        child1 = _normalize_winbuilds(child1)
        
        kmsdb.append(child1)
        
        ## Get csvlkitem data.
        child1 = []
        for csvlk in root.iter('CsvlkItem'):
                for activ in csvlk.iter('Activate'):
                        child2.append(activ.attrib['KmsItem'])
                        csvlk.attrib.update({'Activate' : child2})
                child1.append(csvlk.attrib)
                child2 = []
                
        kmsdb.append(child1)

        ## Get appitem data.
        child1 = []
        for app in root.iter('AppItem'):
                for kms in app.iter('KmsItem'):
                        for sku in kms.iter('SkuItem'):
                                child3.append(sku.attrib)
                        kms.attrib.update({'SkuItems' : child3})
                        child2.append(kms.attrib)
                        child3 = []

                app.attrib.update({'KmsItems' : child2})       
                child1.append(app.attrib)
                child2 = []
                
        kmsdb.append(child1)

        return kmsdb
