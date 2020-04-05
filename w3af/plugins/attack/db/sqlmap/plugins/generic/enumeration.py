#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.common import Backend
from w3af.plugins.attack.db.sqlmap.lib.core.common import unArrayizeValue
from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.data import queries
from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.session import setOs
from w3af.plugins.attack.db.sqlmap.lib.parse.banner import bannerParser
from w3af.plugins.attack.db.sqlmap.lib.request import inject
from w3af.plugins.attack.db.sqlmap.plugins.generic.custom import Custom
from w3af.plugins.attack.db.sqlmap.plugins.generic.databases import Databases
from w3af.plugins.attack.db.sqlmap.plugins.generic.entries import Entries
from w3af.plugins.attack.db.sqlmap.plugins.generic.search import Search
from w3af.plugins.attack.db.sqlmap.plugins.generic.users import Users

class Enumeration(Custom, Databases, Entries, Search, Users):
    """
    This class defines generic enumeration functionalities for plugins.
    """

    def __init__(self):
        kb.data.has_information_schema = False
        kb.data.banner = None
        kb.data.hostname = ""
        kb.data.processChar = None
        kb.data.characterSet = None

        Custom.__init__(self)
        Databases.__init__(self)
        Entries.__init__(self)
        Search.__init__(self)
        Users.__init__(self)

    def getBanner(self):
        if not conf.getBanner:
            return

        if kb.data.banner is None:
            infoMsg = "fetching banner"
            logger.info(infoMsg)

            if Backend.isDbms(DBMS.DB2):
                rootQuery = queries[DBMS.DB2].banner
                for query in (rootQuery.query, rootQuery.query2):
                    kb.data.banner = unArrayizeValue(inject.getValue(query, safeCharEncode=False))
                    if kb.data.banner:
                        break
            else:
                query = queries[Backend.getIdentifiedDbms()].banner.query
                kb.data.banner = unArrayizeValue(inject.getValue(query, safeCharEncode=False))

            bannerParser(kb.data.banner)

            if conf.os and conf.os == "windows":
                kb.bannerFp["type"] = {"Windows"}

            elif conf.os and conf.os == "linux":
                kb.bannerFp["type"] = {"Linux"}

            elif conf.os:
                kb.bannerFp["type"] = {"%s%s" % (conf.os[0].upper(), conf.os[1:])}

            if conf.os:
                setOs()

        return kb.data.banner

    def getHostname(self):
        infoMsg = "fetching server hostname"
        logger.info(infoMsg)

        query = queries[Backend.getIdentifiedDbms()].hostname.query

        if not kb.data.hostname:
            kb.data.hostname = unArrayizeValue(inject.getValue(query, safeCharEncode=False))

        return kb.data.hostname
