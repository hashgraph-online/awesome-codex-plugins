"""Check the actual newly painted prose, including the PDF's native clip.

Layout-engine spare-height success does not prove the fallback font's ink fits.
This check never enlarges a permitted repair island or applies a clip epsilon.
"""
import pdf_objects as objects

VERSION='0.1.0-draft.1'


def glyph_count(page):return sum(len(span['chars']) for span in page.get_texttrace())


def check(page,*,first_glyph=0,require_content=True):
    inventory=objects.inventory(page)
    if type(first_glyph) is not int or not 0<=first_glyph<=len(inventory['glyphs']):raise ValueError('INVALID_NEW_PROSE_GLYPH_BOUNDARY')
    added=inventory['glyphs'][first_glyph:];issues=[];visible=[]
    for g in added:
        if g.get('logical_only') or objects.content_unicode(g).isspace():continue
        if g['visibility'] in {'visible_candidate','partially_clipped'}:visible.append(g)
        if g['shape'] is None or objects.unreadable(g):issues.append({'code':'NEW_PROSE_UNREADABLE_GLYPH','glyph_id':g['id']})
        if g['clip_uncertain'] or g['group_uncertain']:issues.append({'code':'NEW_PROSE_VISIBILITY_UNPROVEN','glyph_id':g['id']})
        if g['visibility']=='partially_clipped':
            if not g.get('clip_ink_evidence',{}).get('all_sampled_ink_inside_clip'):
                issues.append({'code':'NEW_PROSE_CLIPPED_INK','glyph_id':g['id'],'ink_bbox':g['ink_bbox'],'clip_bbox':g['clip_bbox']})
        elif g['visibility']!='visible_candidate':issues.append({'code':'NEW_PROSE_PAINT_NOT_VISIBLE','glyph_id':g['id'],'visibility':g['visibility']})
    if require_content and not visible:issues.append({'code':'NEW_PROSE_PAINT_MISSING'})
    evidence=[{k:g[k] for k in ('id','unicode','shape','font','size','origin','ink_bbox','clip_bbox','visibility','seqno')} for g in added]
    return {'version':VERSION,'passed':not issues,'new_raw_glyphs':len(added),'visible_primary_glyphs':len(visible),
        'issues':issues,'native_paint_sha256':objects.digest(evidence),'native_glyphs':evidence,
        'scope':'Actual current page glyphs after the append boundary; finite clip-mask envelopes, not exact outline or semantic certification.'}
