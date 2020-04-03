#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.settings import PGSQL_SYSTEM_DBS
from w3af.plugins.attack.db.sqlmap.lib.core.unescaper import unescaper
from w3af.plugins.attack.db.sqlmap.plugins.dbms.postgresql.enumeration import Enumeration
from w3af.plugins.attack.db.sqlmap.plugins.dbms.postgresql.filesystem import Filesystem
from w3af.plugins.attack.db.sqlmap.plugins.dbms.postgresql.fingerprint import Fingerprint
from w3af.plugins.attack.db.sqlmap.plugins.dbms.postgresql.syntax import Syntax
from w3af.plugins.attack.db.sqlmap.plugins.dbms.postgresql.takeover import Takeover
from w3af.plugins.attack.db.sqlmap.plugins.generic.misc import Miscellaneous

class PostgreSQLMap(Syntax, Fingerprint, Enumeration, Filesystem, Miscellaneous, Takeover):
    """
    This class defines PostgreSQL methods
    """

    def __init__(self):
        self.excludeDbsList = PGSQL_SYSTEM_DBS
        self.sysUdfs = {
                         # UDF name:     UDF parameters' input data-type and return data-type
                         "sys_exec":     { "input":  ["text"], "return": "int4" },
                         "sys_eval":     { "input":  ["text"], "return": "text" },
                         "sys_bineval":  { "input":  ["text"], "return": "int4" },
                         "sys_fileread": { "input":  ["text"], "return": "text" }
                       }

        Syntax.__init__(self)
        Fingerprint.__init__(self)
        Enumeration.__init__(self)
        Filesystem.__init__(self)
        Miscellaneous.__init__(self)
        Takeover.__init__(self)

    unescaper[DBMS.PGSQL] = Syntax.escape
