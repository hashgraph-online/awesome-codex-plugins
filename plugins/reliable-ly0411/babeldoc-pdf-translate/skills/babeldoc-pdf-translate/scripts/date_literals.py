"""Closed Gregorian literal aliases; never a waiver for extra numeric values.

English named dates and explicit Chinese 年/月/日 forms are typed calendar
literals. A month/year has different precision from a complete day. Unlabelled
numeric ISO forms are optional for legacy audit use; translation guards leave
them numeric so subtraction/model identifiers do not become date exemptions.
"""
import datetime
import re

VERSION='1.1.0-draft.1'
FULL=('January','February','March','April','May','June','July','August',
      'September','October','November','December')
SHORT=('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
MONTHS={name.lower():number for number,pair in enumerate(zip(FULL,SHORT),1) for name in pair}
MONTHS['sept']=9
NAMES='|'.join(sorted(MONTHS,key=len,reverse=True))
TITLES='|'.join(sorted({n for name in MONTHS for n in (name.title(),name.upper())},key=len,reverse=True))
CN=('一','二','三','四','五','六','七','八','九','十','十一','十二','十三','十四','十五',
    '十六','十七','十八','十九','二十','二十一','二十二','二十三','二十四','二十五',
    '二十六','二十七','二十八','二十九','三十','三十一')
CN_VALUES={name:i for i,name in enumerate(CN,1)}
TOKEN=r'(?:[0-9]{1,2}|'+'|'.join(sorted(CN,key=len,reverse=True))+')'
EN_DAY=re.compile(r'(?<![A-Za-z0-9])([0-9]{1,2})\s+('+NAMES+r')\.?\s+([0-9]{4})(?![0-9]|\.[0-9])',re.I)
EN_US=re.compile(r'(?<![A-Za-z0-9])('+NAMES+r')\.?\s+([0-9]{1,2}),?\s+([0-9]{4})(?![0-9]|\.[0-9])',re.I)
ZH_DAY=re.compile(r'(?<![0-9])([0-9]{4})\s*年\s*('+TOKEN+r')\s*月\s*('+TOKEN+r')\s*日(?![0-9])')
ZH_MIXED=re.compile(r'(?<![0-9])('+TOKEN+r')\s+([0-9]{4})\s*年\s*('+TOKEN+r')\s*月(?![0-9])')
MIXED=re.compile(r'(?<![0-9])('+TOKEN+r')\s+('+TOKEN+r')\s*月\s*([0-9]{4})(?![0-9])')
EN_MONTH=re.compile(r'(?<![A-Za-z0-9])('+TITLES+r')\.?\s+([0-9]{4})(?![0-9]|\.[0-9])')
ZH_MONTH=re.compile(r'(?<![0-9])([0-9]{4})\s*年\s*('+TOKEN+r')\s*月')
ZH_MONTH_FIRST=re.compile(r'(?<![0-9])('+TOKEN+r')\s*月\s*([0-9]{4})(?![0-9])')
ISO_DAY=re.compile(r'(?<![0-9])([0-9]{4})[-\u2010\u2011]([0-9]{2})[-\u2010\u2011]([0-9]{2})(?![0-9])')
ISO_MONTH=re.compile(r'(?<![0-9\u2010\u2011-])([0-9]{4})[-\u2010\u2011]([0-9]{2})(?![0-9\u2010\u2011-])')

# A native PDF field remains an opaque identity, never an inferred number.
# Only explicit named-month / Chinese calendar grammar can assign its role.
OPAQUE=r'\{v[0-9]+\}'
FIELD_YEAR=r'(?:[0-9]{4}|'+OPAQUE+r')'
FIELD_DAY=r'(?:'+TOKEN+r'|'+OPAQUE+r')'
START=r'(?<![A-Za-z0-9_+\-\u2212])'
END=r'(?![A-Za-z0-9_]|\.[0-9])'
EN_FIELDS_DAY=re.compile(START+'('+FIELD_DAY+r')\s+('+TITLES+r')\.?\s*('+FIELD_YEAR+')'+END)
EN_FIELDS_US=re.compile(START+'('+TITLES+r')\.?\s+('+FIELD_DAY+r')(?:,\s*|\s+)('+FIELD_YEAR+')'+END)
EN_FIELDS_MONTH=re.compile(START+'('+TITLES+r')\.?\s*('+FIELD_YEAR+')'+END)
ZH_FIELDS_DAY=re.compile(START+'('+FIELD_YEAR+r')\s*年\s*('+TOKEN+r')\s*月\s*('+FIELD_DAY+r')\s*日'+END)
ZH_FIELDS_DAY_FIRST=re.compile(START+'('+TOKEN+r')\s*月\s*('+FIELD_DAY+r')\s*日\s*('+FIELD_YEAR+r')(?:\s*年)?'+END)
ZH_FIELDS_MONTH=re.compile(START+'('+FIELD_YEAR+r')\s*年\s*('+TOKEN+r')\s*月'+END)
ZH_FIELDS_MONTH_FIRST=re.compile(START+'('+TOKEN+r')\s*月\s*('+FIELD_YEAR+r')(?:\s*年)?'+END)
ZH_OPAQUE_MONTH=re.compile(START+'('+OPAQUE+r')\s*(?:年\s*)?('+TOKEN+r')\s*月'+END)
ZH_OPAQUE_DAY=re.compile(START+'('+OPAQUE+r')\s*(?:年\s*)?('+TOKEN+r')\s*月\s*('+FIELD_DAY+r')\s*日'+END)
ZH_OPAQUE_MONTH_FIRST=re.compile(START+'('+TOKEN+r')\s*月份\s*('+OPAQUE+r')(?:\s*年)?'+END)


def integer(value):return CN_VALUES[value] if value in CN_VALUES else int(value)


def field(value):return value if re.fullmatch(OPAQUE,value) else integer(value)


def fact(year,month,day,precision):
    opaque=[v for v in (year,day) if isinstance(v,str)]
    if len(set(opaque))!=len(opaque):raise ValueError('Repeated date field identity')
    # A hidden year is not decoded. Leap-year validation with 2000 admits Feb29
    # only as a possible date, while rejecting impossible month/day pairs.
    datetime.date(2000 if isinstance(year,str) else year,month,1 if isinstance(day,str) else day)
    if not opaque:
        value=datetime.date(year,month,day)
        return value.isoformat() if precision=='day' else 'month:%04d-%02d'%(year,month)
    return 'calendar:'+precision+':year='+str(year)+';month='+str(month)+('' if precision=='month' else ';day='+str(day))


def extract(text,*,numeric_iso=True,opaque_fields=False,record_spans=None):
    spans=[];invalid=[];ordered=[]
    def add(pattern,decode,precision='day',*,require_opaque=False):
        for match in pattern.finditer(text):
            if any(a<match.end() and match.start()<b for a,b in spans+invalid):continue
            year,month,day=decode(match)
            if require_opaque and not any(isinstance(v,str) for v in (year,day)):continue
            prefix=text[:match.start()]
            if re.search(r'\b(?:vol(?:ume)?\.?|issue|no\.?|number|page|pp?\.?)\s*[:#]?\s*$',prefix,re.I):continue
            if re.search(r'(?:编号|卷号|期号|页码|第)\s*[:：]?\s*$',prefix):continue
            if match[0].startswith('{v') and re.search(r'[=+*/^_<>\u2264\u2265]\s*$',prefix):continue
            if require_opaque and pattern in (EN_FIELDS_US,EN_FIELDS_MONTH):
                # "May {v1} be independent?" / "March {v1} steps" are
                # modal/verb prose, not dates. A continued English sentence
                # needs an explicit calendar preposition before this fragment.
                tail=text[match.end():].lstrip()
                if (re.match(r'[A-Za-z]',tail) and not re.search(
                    r'\b(?:in|on|during|since|until|by|before|after|through|from|dated|as of)\s*$',text[:match.start()],re.I)):
                    continue
            # Signed/identifier-attached components cannot acquire a date
            # exemption, even when a longer pattern starts after a sign.
            if match.start() and text[match.start()-1] in '+-\u2212_':continue
            try:value=fact(year,month,day,precision)
            except ValueError:
                # An impossible full date must not be reinterpreted as a valid
                # month plus an unrelated scalar day by a shorter pattern.
                invalid.append(match.span());continue
            ordered.append((match.start(),value))
            spans.append(match.span())
            if record_spans is not None:record_spans.append((match.start(),match.end(),value))
    if opaque_fields:
        add(EN_FIELDS_DAY,lambda m:(field(m[3]),MONTHS[m[2].lower()],field(m[1])),require_opaque=True)
        add(EN_FIELDS_US,lambda m:(field(m[3]),MONTHS[m[1].lower()],field(m[2])),require_opaque=True)
        add(ZH_FIELDS_DAY,lambda m:(field(m[1]),integer(m[2]),field(m[3])),require_opaque=True)
        add(ZH_FIELDS_DAY_FIRST,lambda m:(field(m[3]),integer(m[1]),field(m[2])),require_opaque=True)
        add(ZH_OPAQUE_DAY,lambda m:(field(m[1]),integer(m[2]),field(m[3])),require_opaque=True)
        add(EN_FIELDS_MONTH,lambda m:(field(m[2]),MONTHS[m[1].lower()],1),'month',require_opaque=True)
        add(ZH_FIELDS_MONTH,lambda m:(field(m[1]),integer(m[2]),1),'month',require_opaque=True)
        add(ZH_FIELDS_MONTH_FIRST,lambda m:(field(m[2]),integer(m[1]),1),'month',require_opaque=True)
        add(ZH_OPAQUE_MONTH,lambda m:(field(m[1]),integer(m[2]),1),'month',require_opaque=True)
        add(ZH_OPAQUE_MONTH_FIRST,lambda m:(field(m[2]),integer(m[1]),1),'month',require_opaque=True)
    add(EN_DAY,lambda m:(int(m[3]),MONTHS[m[2].lower()],int(m[1])))
    add(EN_US,lambda m:(int(m[3]),MONTHS[m[1].lower()],int(m[2])))
    add(ZH_DAY,lambda m:(int(m[1]),integer(m[2]),integer(m[3])))
    add(ZH_MIXED,lambda m:(int(m[2]),integer(m[3]),integer(m[1])))
    add(MIXED,lambda m:(int(m[3]),integer(m[2]),integer(m[1])))
    if numeric_iso:add(ISO_DAY,lambda m:(int(m[1]),int(m[2]),int(m[3])))
    add(EN_MONTH,lambda m:(int(m[2]),MONTHS[m[1].lower()],1),'month')
    add(ZH_MONTH,lambda m:(int(m[1]),integer(m[2]),1),'month')
    add(ZH_MONTH_FIRST,lambda m:(int(m[2]),integer(m[1]),1),'month')
    if numeric_iso:add(ISO_MONTH,lambda m:(int(m[1]),int(m[2]),1),'month')
    remaining=list(text)
    for start,stop in spans:remaining[start:stop]=' '*(stop-start)
    return [fact for _,fact in sorted(ordered)],''.join(remaining)


def visible_text(text,markers):
    removed=set()
    for match in markers.finditer(text):
        if match[0].startswith('<'):removed.update(range(match.start(),match.end()))
    positions=[i for i in range(len(text)) if i not in removed]
    return ''.join(text[i] for i in positions),positions


def opaque_groups(text,markers):
    """Original positions of day/year fields in the SAME recognized date.

    Only multi-field calendar grammar distinguishes its separating comma from
    mathematical syntax. A date followed by +, -, a tuple, or another formula
    does not acquire this exception.
    """
    visible,positions=visible_text(text,markers);spans=[]
    extract(visible,numeric_iso=False,opaque_fields=True,record_spans=spans)
    groups=[]
    for start,end,value in spans:
        if not value.startswith('calendar:'):continue
        fields={positions[m.start()] for m in re.finditer(OPAQUE,visible) if start<=m.start() and m.end()<=end}
        if len(fields)>1:groups.append(fields)
    return groups


def protected(text,markers):
    """Extract before erasing opaque fields; styles are presentation only.

    Calendar facts retain each hidden day/year's exact marker identity. Marker
    order and mathematical structure are still enforced by the caller. No
    marker-free standalone month or ambiguous numeric date is guessed.
    """
    visible,_=visible_text(text,markers)
    values,remainder=extract(visible,numeric_iso=False,opaque_fields=True)
    return values,markers.sub('',remainder)
