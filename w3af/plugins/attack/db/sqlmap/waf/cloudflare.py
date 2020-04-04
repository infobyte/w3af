#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re

from w3af.plugins.attack.db.sqlmap.lib.core.enums import HTTP_HEADER
from w3af.plugins.attack.db.sqlmap.lib.core.settings import WAF_ATTACK_VECTORS

__product__ = "CloudFlare Web Application Firewall (CloudFlare)"

def detect(get_page):
    retval = False

    for vector in WAF_ATTACK_VECTORS:
        page, headers, code = get_page(get=vector)
        retval = re.search(r"cloudflare-nginx", headers.get(HTTP_HEADER.SERVER, ""), re.I) is not None

        if code >= 400:
            retval |= re.search(r"\A__cfduid=", headers.get(HTTP_HEADER.SET_COOKIE, ""), re.I) is not None
            retval |= headers.get("cf-ray") is not None
            retval |= re.search(r"CloudFlare Ray ID:|var CloudFlare=", page or "") is not None

        if retval:
            break

    return retval
