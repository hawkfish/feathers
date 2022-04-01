import re
import unittest

pg_code = {
    'HH': 'HH',         # hour of day (01–12)
    'HH12': 'HH12',     # hour of day (01–12)
    'HH24': 'HH24',     # hour of day (00–23)
    'MI': 'MI',         # minute (00–59)
    'SS': 'SS',         # second (00–59)
    'MS': 'MS',         # millisecond (000–999)
    'US': 'US',         # microsecond (000000–999999)
    'FF1': 'FF1',       # tenth of second (0–9)
    'FF2': 'FF2',       # hundredth of second (00–99)
    'FF3': 'FF3',       # millisecond (000–999)
    'FF4': 'FF4',       # tenth of a millisecond (0000–9999)
    'FF5': 'FF5',       # hundredth of a millisecond (00000–99999)
    'FF6': 'FF6',       # microsecond (000000–999999)
    'SSSS': 'SSSS',     # seconds past midnight (0–86399)
    'SSSSS': 'SSSSS',   # seconds past midnight (0–86399)
    'AM': 'AM',         # meridiem indicator (without periods)
    'am': 'AM',         # meridiem indicator (without periods)
    'PM': 'AM',         # meridiem indicator (without periods)
    'pm': 'AM',         # meridiem indicator (without periods)
    'A.M.': 'A.M.',     # meridiem indicator (with periods)
    'a.m.': 'A.M.',     # meridiem indicator (with periods)
    'P.M.': 'A.M.',     # meridiem indicator (with periods)
    'p.m.': 'A.M.',     # meridiem indicator (with periods)
    'Y,YYY': 'Y,YYY',   # year (4 or more digits) with comma
    'YYYY': 'YYYY',     # year (4 or more digits)
    'YYY': 'YYY',       # last 3 digits of year
    'YY': 'YY',         # last 2 digits of year
    'Y': 'Y',           # last digit of year
    'IYYY': 'IYYY',     # ISO 8601 week-numbering year (4 or more digits)
    'IYY': 'IYY',       # last 3 digits of ISO 8601 week-numbering year
    'IY': 'IY',         # last 2 digits of ISO 8601 week-numbering year
    'I': 'I',           # last digit of ISO 8601 week-numbering year
    'BC': 'AD',         # era indicator (without periods)
    'bc,': 'AD',        # era indicator (without periods)
    'AD,': 'AD',        # era indicator (without periods)
    'ad,': 'AD',        # era indicator (without periods)
    'B.C.': 'A.D.',     # era indicator (with periods)
    'b.c.': 'A.D.',     # era indicator (with periods)
    'A.D.': 'A.D.',     # era indicator (with periods)
    'a.d.': 'A.D.',     # era indicator (with periods)
    'MONTH': 'MONTH',   # full upper case month name (blank-padded to 9 chars)
    'Month': 'Month',   # full capitalized month name (blank-padded to 9 chars)
    'month': 'month',   # full lower case month name (blank-padded to 9 chars)
    'MON': 'MON',       # abbreviated upper case month name (3 chars in English, localized lengths vary)
    'Mon': 'Mon',       # abbreviated capitalized month name (3 chars in English, localized lengths vary)
    'mon': 'mon',       # abbreviated lower case month name (3 chars in English, localized lengths vary)
    'MM': 'MM',         # month number (01–12)
    'DAY': 'DAY',       # full upper case day name (blank-padded to 9 chars)
    'Day': 'Day',       # full capitalized day name (blank-padded to 9 chars)
    'day': 'day',       # full lower case day name (blank-padded to 9 chars)
    'DY': 'DY',         # abbreviated upper case day name (3 chars in English, localized lengths vary)
    'Dy': 'Dy',         # abbreviated capitalized day name (3 chars in English, localized lengths vary)
    'dy': 'dy',         # abbreviated lower case day name (3 chars in English, localized lengths vary)
    'DDD': 'DDD',       # day of year (001–366)
    'IDDD': 'IDDD',     # day of ISO 8601 week-numbering year (001–371; day 1 of the year is Monday of the first ISO week)
    'DD': 'DD',         # day of month (01–31)
    'D': 'D',           # day of the week, Sunday (1) to Saturday (7)
    'ID': 'ID',         # ISO 8601 day of the week, Monday (1) to Sunday (7)
    'W': 'W',           # week of month (1–5) (the first week starts on the first day of the month)
    'WW': 'WW',         # week number of year (1–53) (the first week starts on the first day of the year)
    'IW': 'IW',         # week number of ISO 8601 week-numbering year (01–53; the first Thursday of the year is in week 1)
    'CC': 'CC',         # century (2 digits) (the twenty-first century starts on 2001-01-01)
    'J': 'J',           # Julian Date (integer days since November 24, 4714 BC at local midnight; see Section B.7)
    'Q': 'Q',           # quarter
    'RM': 'RM',         # month in upper case Roman numerals (I–XII; I=January)
    'rm': 'rm',         # month in lower case Roman numerals (i–xii; i=January)
    'TZ': 'TZ',         # upper case time-zone abbreviation (only supported in to_char)
    'tz': 'tz',         # lower case time-zone abbreviation (only supported in to_char)
    'TZH': 'TZH',       # time-zone hours
    'TZM': 'TZM',       # time-zone minutes
    'OF': 'OF',         # time-zone offset from UTC (only supported in to_char)
}

pg_prefixes = {
    'FM': 'FM',         # fill mode (suppress leading zeroes and padding blanks) - FMMonth
    'TM': 'TM',         # translation mode (use localized day and month names based on lc_time) - TMMonth
}

pg_globals = {
    'FX': 'FX',         # fixed format global option (see usage notes) - FX Month DD Day
}

pg_suffixes = {
    'TH': 'TH',         # upper case ordinal number suffix - DDTH, e.g., 12TH
    'th': 'th',         # lower case ordinal number suffix - DDth, e.g., 12th
    'SP': 'SP',         # spell mode (not implemented) - DDSP
}

pg_seps = re.compile(r'[ A-Za-z\d]+')

def starts_with_prefix(s, d, begin = 0):
    matches = [d[prefix] for prefix in d.keys() if s.startswith(prefix, begin)]
    if matches:
        return matches[0]
    return ''

def pg_parse(fmt):
    templates = []

    pos = 0
    g = starts_with_prefix(fmt, pg_globals, pos)
    pos += len(g)
    while pos < len(fmt):
        template = {'prefix': '', 'code': '', 'suffix': ''}

        # Separator?
        seps = pg_seps.match(fmt, pos)
        if seps:
            template['code'] = seps.group()
            templates.append(template)
            pos += seps.end() - seps.start()
            continue

        # Prefix?
        prefix = starts_with_prefix(fmt, pg_prefixes, pos)
        template['prefix'] = prefix
        pos += len(prefix)

        # Format code
        code = starts_with_prefix(fmt, pg_codes, pos)
        if not code:
            raise f"Unknown format code at position {pos}"
        template['code'] = code
        pos += len(code)

        # Suffix?
        suffix = starts_with_prefix(fmt, pg_suffixes, pos)
        template['suffix'] = suffix
        pos += len(suffix)

        templates.append(template)

    return {'globals': g, 'templates': templates}

def pg_format(parsed):
    parts = []
    parts.append(parsed['globals'])
    for template in parsed['templates']:
        parts.append(template['prefix'])
        parts.append(template['code'])
        parts.append(template['suffix'])
    return ''.join(parts)

class TestPGTimes(unittest.TestCase):

    def assertRoundTrip(self, setup, expected = None):
        if not expected: expected = setup

        actual = pg_format(pg_parse(setup))
        self.assertEqual(expected, actual)

    def test_documentation(self):
        self.assertRoundTrip('DD Mon YYYY')
        self.assertRoundTrip('FMMonth')
        self.assertRoundTrip('DDTH')
        self.assertRoundTrip('DDth')
        self.assertRoundTrip('FX Month DD Day')
        self.assertRoundTrip('TMMonth')
        self.assertRoundTrip('TMMonth')
        self.assertRoundTrip('DDSP')

if __name__ == '__main__':
    unittest.main()
