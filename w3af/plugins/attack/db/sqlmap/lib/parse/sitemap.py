#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import http.client
import re

from w3af.plugins.attack.db.sqlmap.lib.core.common import readInput
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.exception import SqlmapSyntaxException
from w3af.plugins.attack.db.sqlmap.lib.request.connect import Connect as Request
from w3af.plugins.attack.db.sqlmap.thirdparty.oset.pyoset import oset

abortedFlag = None

def parseSitemap(url, retVal=None):
    global abortedFlag

    if retVal is not None:
        logger.debug("parsing sitemap '%s'" % url)

    try:
        if retVal is None:
            abortedFlag = False
            retVal = oset()

        try:
            content = Request.getPage(url=url, raise404=True)[0] if not abortedFlag else ""
        except http.client.InvalidURL:
            errMsg = "invalid URL given for sitemap ('%s')" % url
            raise SqlmapSyntaxException(errMsg)

        for match in re.finditer(r"<loc>\s*([^<]+)", content or ""):
            if abortedFlag:
                break
            url = match.group(1).strip()
            if url.endswith(".xml") and "sitemap" in url.lower():
                if kb.followSitemapRecursion is None:
                    message = "sitemap recursion detected. Do you want to follow? [y/N] "
                    kb.followSitemapRecursion = readInput(message, default='N', boolean=True)
                if kb.followSitemapRecursion:
                    parseSitemap(url, retVal)
            else:
                retVal.add(url)

    except KeyboardInterrupt:
        abortedFlag = True
        warnMsg = "user aborted during sitemap parsing. sqlmap "
        warnMsg += "will use partial list"
        logger.warn(warnMsg)

    return retVal
