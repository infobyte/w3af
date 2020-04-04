#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re

from w3af.plugins.attack.db.sqlmap.lib.core.enums import HTTP_HEADER
from w3af.plugins.attack.db.sqlmap.lib.core.settings import WAF_ATTACK_VECTORS

__product__ = "Safe3 Web Application Firewall"

def detect(get_page):
    retval = False

    for vector in WAF_ATTACK_VECTORS:
        _, headers, _ = get_page(get=vector)
        retval = re.search(r"Safe3WAF", headers.get(HTTP_HEADER.X_POWERED_BY, ""), re.I) is not None
        retval |= re.search(r"Safe3 Web Firewall", headers.get(HTTP_HEADER.SERVER, ""), re.I) is not None
        if retval:
            break

    return retval

