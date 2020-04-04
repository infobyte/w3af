#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re

from w3af.plugins.attack.db.sqlmap.lib.core.enums import HTTP_HEADER
from w3af.plugins.attack.db.sqlmap.lib.core.settings import WAF_ATTACK_VECTORS

__product__ = "FortiWeb Web Application Firewall (Fortinet)"

def detect(get_page):
    retval = False

    for vector in WAF_ATTACK_VECTORS:
        page, headers, _ = get_page(get=vector)
        retval = re.search(r"\AFORTIWAFSID=", headers.get(HTTP_HEADER.SET_COOKIE, ""), re.I) is not None
        retval |= all(_ in (page or "") for _ in (".fgd_icon", ".blocked", ".authenticate"))
        if retval:
            break

    return retval
