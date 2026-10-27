"""Conservative unchanged-English sentence screen for an explicit Chinese target.

This is an omission warning, not a semantic equivalence or general language
detector. Proper names, code, references and bilingual terminology are negatives.
All geometry is supplied by the program; this module never edits a PDF.
"""
import re,unicodedata

WORD=re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
CJK=re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
COPULA={'is','are','was','were'}


def normalized(text):
    value=unicodedata.normalize('NFKC',text).replace('’',"'")
    value=re.sub(r'(?<=[a-z])-\s*\n\s*(?=[a-z])','',value)
    return re.sub(r'\s+',' ',value).strip()


def ordinary_english_sentence(text):
    if CJK.search(text) or re.search(r'`|https?://|\bwww\.|\bdoi\b|[\w.+-]+@[\w.-]+',text,re.I):return False
    words=WORD.findall(text)
    if len(words)<5 or not any(w in COPULA for w in words):return False
    # Capitalized personal names and title-style metadata are not prose proof.
    if sum(w[0].isupper() for w in words)/len(words)>=.5:return False
    # Strong bibliography evidence, not a blanket exemption for [N] citations.
    if re.search(r'\b(?:19|20)\d{2}\b',text) and re.search(r'\b(?:vol\.|pp\.|ISBN|IEEE|ACM)\b',text):return False
    return True


def unchanged_english(source,target):
    """Exact normalized ordinary prose retained in an explicit Chinese output."""
    if not ordinary_english_sentence(target):return False
    needle=normalized(target);haystack=normalized(source)
    return bool(needle and haystack.count(needle)==1)


def findings(source_page,target_regions):
    original=source_page.get_text()
    issues=[]
    for region in target_regions:
        if unchanged_english(original,region['text']):
            issues.append({'region_id':region['id'],'category':'missing_translation','severity':'major',
                'replacement':'','reason':'Program Chinese-target completeness screen: a complete ordinary English sentence remains unchanged from the source. Translation or explicit human adjudication is required.'})
    return issues
