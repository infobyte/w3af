#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.settings import INFORMIX_SYSTEM_DBS
from w3af.plugins.attack.db.sqlmap.lib.core.unescaper import unescaper
from w3af.plugins.attack.db.sqlmap.plugins.dbms.informix.enumeration import Enumeration
from w3af.plugins.attack.db.sqlmap.plugins.dbms.informix.filesystem import Filesystem
from w3af.plugins.attack.db.sqlmap.plugins.dbms.informix.fingerprint import Fingerprint
from w3af.plugins.attack.db.sqlmap.plugins.dbms.informix.syntax import Syntax
from w3af.plugins.attack.db.sqlmap.plugins.dbms.informix.takeover import Takeover
from w3af.plugins.attack.db.sqlmap.plugins.generic.misc import Miscellaneous


class InformixMap(Syntax, Fingerprint, Enumeration, Filesystem, Miscellaneous, Takeover):
    """
    This class defines Informix methods
    """

    def __init__(self):
        self.excludeDbsList = INFORMIX_SYSTEM_DBS

        Syntax.__init__(self)
        Fingerprint.__init__(self)
        Enumeration.__init__(self)
        Filesystem.__init__(self)
        Miscellaneous.__init__(self)
        Takeover.__init__(self)

    unescaper[DBMS.INFORMIX] = Syntax.escape
