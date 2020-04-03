#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MAXDB_SYSTEM_DBS
from w3af.plugins.attack.db.sqlmap.lib.core.unescaper import unescaper
from w3af.plugins.attack.db.sqlmap.plugins.dbms.maxdb.enumeration import Enumeration
from w3af.plugins.attack.db.sqlmap.plugins.dbms.maxdb.filesystem import Filesystem
from w3af.plugins.attack.db.sqlmap.plugins.dbms.maxdb.fingerprint import Fingerprint
from w3af.plugins.attack.db.sqlmap.plugins.dbms.maxdb.syntax import Syntax
from w3af.plugins.attack.db.sqlmap.plugins.dbms.maxdb.takeover import Takeover
from w3af.plugins.attack.db.sqlmap.plugins.generic.misc import Miscellaneous


class MaxDBMap(Syntax, Fingerprint, Enumeration, Filesystem, Miscellaneous, Takeover):
    """
    This class defines SAP MaxDB methods
    """

    def __init__(self):
        self.excludeDbsList = MAXDB_SYSTEM_DBS

        Syntax.__init__(self)
        Fingerprint.__init__(self)
        Enumeration.__init__(self)
        Filesystem.__init__(self)
        Miscellaneous.__init__(self)
        Takeover.__init__(self)

    unescaper[DBMS.MAXDB] = Syntax.escape
