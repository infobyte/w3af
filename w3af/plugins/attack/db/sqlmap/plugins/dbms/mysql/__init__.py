#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MYSQL_SYSTEM_DBS
from w3af.plugins.attack.db.sqlmap.lib.core.unescaper import unescaper
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mysql.enumeration import Enumeration
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mysql.filesystem import Filesystem
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mysql.fingerprint import Fingerprint
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mysql.syntax import Syntax
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mysql.takeover import Takeover
from w3af.plugins.attack.db.sqlmap.plugins.generic.misc import Miscellaneous


class MySQLMap(Syntax, Fingerprint, Enumeration, Filesystem, Miscellaneous, Takeover):
    """
    This class defines MySQL methods
    """

    def __init__(self):
        self.excludeDbsList = MYSQL_SYSTEM_DBS
        self.sysUdfs = {
                         # UDF name:    UDF return data-type
                         "sys_exec":    { "return": "int" },
                         "sys_eval":    { "return": "string" },
                         "sys_bineval": { "return": "int" }
                       }

        Syntax.__init__(self)
        Fingerprint.__init__(self)
        Enumeration.__init__(self)
        Filesystem.__init__(self)
        Miscellaneous.__init__(self)
        Takeover.__init__(self)

    unescaper[DBMS.MYSQL] = Syntax.escape
