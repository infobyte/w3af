#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re

from w3af.plugins.attack.db.sqlmap.lib.core.common import Backend
from w3af.plugins.attack.db.sqlmap.lib.core.common import Format
from w3af.plugins.attack.db.sqlmap.lib.core.common import hashDBWrite
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.enums import HASHDB_KEYS
from w3af.plugins.attack.db.sqlmap.lib.core.enums import OS
from w3af.plugins.attack.db.sqlmap.lib.core.settings import SUPPORTED_DBMS

def setDbms(dbms):
    """
    @param dbms: database management system to be set into the knowledge
    base as fingerprint.
    @type dbms: C{str}
    """

    hashDBWrite(HASHDB_KEYS.DBMS, dbms)

    _ = "(%s)" % ("|".join([alias for alias in SUPPORTED_DBMS]))
    _ = re.search(r"\A%s( |\Z)" % _, dbms, re.I)

    if _:
        dbms = _.group(1)

    Backend.setDbms(dbms)
    if kb.resolutionDbms:
        hashDBWrite(HASHDB_KEYS.DBMS, kb.resolutionDbms)

    logger.info("the back-end DBMS is %s" % Backend.getDbms())

def setOs():
    """
    Example of kb.bannerFp dictionary:

    {
      'sp': set(['Service Pack 4']),
      'dbmsVersion': '8.00.194',
      'dbmsServicePack': '0',
      'distrib': set(['2000']),
      'dbmsRelease': '2000',
      'type': set(['Windows'])
    }
    """

    infoMsg = ""

    if not kb.bannerFp:
        return

    if "type" in kb.bannerFp:
        Backend.setOs(Format.humanize(kb.bannerFp["type"]))
        infoMsg = "the back-end DBMS operating system is %s" % Backend.getOs()

    if "distrib" in kb.bannerFp:
        kb.osVersion = Format.humanize(kb.bannerFp["distrib"])
        infoMsg += " %s" % kb.osVersion

    if "sp" in kb.bannerFp:
        kb.osSP = int(Format.humanize(kb.bannerFp["sp"]).replace("Service Pack ", ""))

    elif "sp" not in kb.bannerFp and Backend.isOs(OS.WINDOWS):
        kb.osSP = 0

    if Backend.getOs() and kb.osVersion and kb.osSP:
        infoMsg += " Service Pack %d" % kb.osSP

    if infoMsg:
        logger.info(infoMsg)

    hashDBWrite(HASHDB_KEYS.OS, Backend.getOs())
