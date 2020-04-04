#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.common import Backend
from w3af.plugins.attack.db.sqlmap.lib.core.common import randomInt
from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.dicts import FROM_DUMMY_TABLE
from w3af.plugins.attack.db.sqlmap.lib.core.exception import SqlmapNotVulnerableException
from w3af.plugins.attack.db.sqlmap.lib.techniques.dns.use import dnsUse


def dnsTest(payload):
    logger.info("testing for data retrieval through DNS channel")

    randInt = randomInt()
    kb.dnsTest = dnsUse(payload, "SELECT %d%s" % (randInt, FROM_DUMMY_TABLE.get(Backend.getIdentifiedDbms(), ""))) == str(randInt)

    if not kb.dnsTest:
        errMsg = "data retrieval through DNS channel failed"
        if not conf.forceDns:
            conf.dnsDomain = None
            errMsg += ". Turning off DNS exfiltration support"
            logger.error(errMsg)
        else:
            raise SqlmapNotVulnerableException(errMsg)
    else:
        infoMsg = "data retrieval through DNS channel was successful"
        logger.info(infoMsg)
