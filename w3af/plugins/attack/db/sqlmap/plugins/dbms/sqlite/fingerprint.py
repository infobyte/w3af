#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.common import Backend
from w3af.plugins.attack.db.sqlmap.lib.core.common import Format
from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.session import setDbms
from w3af.plugins.attack.db.sqlmap.lib.core.settings import METADB_SUFFIX
from w3af.plugins.attack.db.sqlmap.lib.core.settings import SQLITE_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.request import inject
from w3af.plugins.attack.db.sqlmap.plugins.generic.fingerprint import Fingerprint as GenericFingerprint

class Fingerprint(GenericFingerprint):
    def __init__(self):
        GenericFingerprint.__init__(self, DBMS.SQLITE)

    def getFingerprint(self):
        value = ""
        wsOsFp = Format.getOs("web server", kb.headersFp)

        if wsOsFp:
            value += "%s\n" % wsOsFp

        if kb.data.banner:
            dbmsOsFp = Format.getOs("back-end DBMS", kb.bannerFp)

            if dbmsOsFp:
                value += "%s\n" % dbmsOsFp

        value += "back-end DBMS: "

        if not conf.extensiveFp:
            value += DBMS.SQLITE
            return value

        actVer = Format.getDbms()
        blank = " " * 15
        value += "active fingerprint: %s" % actVer

        if kb.bannerFp:
            banVer = kb.bannerFp["dbmsVersion"]
            banVer = Format.getDbms([banVer])
            value += "\n%sbanner parsing fingerprint: %s" % (blank, banVer)

        htmlErrorFp = Format.getErrorParsedDBMSes()

        if htmlErrorFp:
            value += "\n%shtml error message fingerprint: %s" % (blank, htmlErrorFp)

        return value

    def checkDbms(self):
        """
        References for fingerprint:

        * http://www.sqlite.org/lang_corefunc.html
        * http://www.sqlite.org/cvstrac/wiki?p=LoadableExtensions
        """

        if not conf.extensiveFp and Backend.isDbmsWithin(SQLITE_ALIASES):
            setDbms(DBMS.SQLITE)

            self.getBanner()

            return True

        infoMsg = "testing %s" % DBMS.SQLITE
        logger.info(infoMsg)

        result = inject.checkBooleanExpression("LAST_INSERT_ROWID()=LAST_INSERT_ROWID()")

        if result:
            infoMsg = "confirming %s" % DBMS.SQLITE
            logger.info(infoMsg)

            result = inject.checkBooleanExpression("SQLITE_VERSION()=SQLITE_VERSION()")

            if not result:
                warnMsg = "the back-end DBMS is not %s" % DBMS.SQLITE
                logger.warn(warnMsg)

                return False
            else:
                infoMsg = "actively fingerprinting %s" % DBMS.SQLITE
                logger.info(infoMsg)

                result = inject.checkBooleanExpression("RANDOMBLOB(-1)>0")
                version = '3' if result else '2'
                Backend.setVersion(version)

            setDbms(DBMS.SQLITE)

            self.getBanner()

            return True
        else:
            warnMsg = "the back-end DBMS is not %s" % DBMS.SQLITE
            logger.warn(warnMsg)

            return False

    def forceDbmsEnum(self):
        conf.db = "%s%s" % (DBMS.SQLITE, METADB_SUFFIX)
