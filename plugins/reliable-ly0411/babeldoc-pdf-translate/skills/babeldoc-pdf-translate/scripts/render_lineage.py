"""Observe actual renderer operations and bind them to saved PDF objects.

The controller and its local evidence folder are trusted. Hashes bind bytes,
not authorship or semantic truth. A recorded cover is a renderer-owned paint;
copied source graphics retain unresolved roles and never get a blanket waiver.
"""
from pathlib import Path
import hashlib,json,math,os,uuid,struct
import pymupdf as fitz
import pdf_objects as objects
from engine_source_map import native_float,float32_step

VERSION='0.1.0-draft.2'
LIMIT=64*1024*1024
# Two native PDF affine roundtrips may accumulate more than four float32
# steps. Bound position error in physical page units instead: <0.35 micrometre,
# or <0.004 pixel at 288 dpi. Font size and every non-position paint attribute
# retain their existing checks. This is not a clipping or semantic waiver.
POSITION_ROUNDING_PT=1/1024


def descriptor(g):
    return {k:g[k] for k in ('unicode','shape','font','size','origin','ink_bbox','clip_bbox','paint_type','opacity','color','direction','clip_uncertain','group_uncertain','visibility')}


def same_paint(a,b):
    if not a['shape'] or a['shape']!=b['shape'] or a['unicode']!=b['unicode']:return False
    if objects.font_key(a['font'])!=objects.font_key(b['font']):return False
    if any(a[k]!=b[k] for k in ('paint_type','opacity','color','direction')):return False
    if abs(a['size']-b['size'])>4*float32_step(a['size']):return False
    return all(math.isfinite(x) and math.isfinite(y) and abs(x-y)<=POSITION_ROUNDING_PT
        for x,y in zip(a['origin'],b['origin']))


def next32(value,up):
    value=native_float(value)
    if value==0:return 2**-149 if up else -2**-149
    bits=struct.unpack('I',struct.pack('f',value))[0]
    return struct.unpack('f',struct.pack('I',bits+(1 if (value>0)==up else -1)))[0]


def inward32(value,lower):
    rounded=native_float(value)
    return next32(rounded,lower) if (rounded<value if lower else rounded>value) else rounded


def opaque_cover(page,area):
    """Write an isolated white fill with float32-roundtrip PDF coordinates.

    Default six-significant-digit shape formatting can move a boundary. Round
    the native frame and PDF operands inward, then observe the actual paint.
    This changes the writer, not an audit tolerance; no paint may leave area.
    """
    area=fitz.Rect(area)
    ptm=page.transformation_matrix
    if (page.rotation or area.is_empty or not page.rect.contains(area) or not all(math.isfinite(x) for x in area)
        or tuple(ptm)[:4]!=(1.,0.,0.,-1.)):raise ValueError('UNSUPPORTED_COVER_FRAME')
    intended=fitz.Rect(inward32(area.x0,True),inward32(area.y0,True),inward32(area.x1,False),inward32(area.y1,False))
    # Rect * Matrix delegates to float32 and can erase an inward step before
    # the PDF is written. Evaluate this supported inverse in double precision.
    pdf=fitz.Rect(intended.x0-ptm.e,ptm.f-intended.y1,intended.x1-ptm.e,ptm.f-intended.y0)
    pdf=fitz.Rect(inward32(pdf.x0,True),inward32(pdf.y0,True),inward32(pdf.x1,False),inward32(pdf.y1,False))
    vals=[pdf.x0,pdf.y0,inward32(pdf.width,False),inward32(pdf.height,False)]
    if intended.is_empty or pdf.is_empty or min(vals[2:])<=0:raise ValueError('COVER_FRAME_NOT_REPRESENTABLE')
    stream=('q 1 1 1 rg '+' '.join(format(x,'.9g') for x in vals)+' re f Q\n').encode()
    page.wrap_contents();doc=page.parent;ref=doc.get_new_xref();doc.update_object(ref,'<< >>');doc.update_stream(ref,stream)
    contents=page.get_contents()+[ref]
    doc.xref_set_key(page.xref,'Contents','['+' '.join(str(x)+' 0 R' for x in contents)+']')
    inventory=objects.inventory(page);path=inventory['vector_paths'][-1]
    if (path['drawing']['type']!='f' or path['drawing']['fill']!=[1.,1.,1.]
        or path['drawing']['fill_opacity']!=1 or not path['native_opaque_rectangle']
        or not area.contains(fitz.Rect(path['bbox'])) or fitz.Rect(path['bbox']).is_empty):
        raise ValueError('COVER_NATIVE_FRAME_CHANGED')
    return {'kind':'renderer_owned_opaque_cover','vector_id':path['id'],'geometry_sha256':path['geometry_sha256'],
        'native_bbox':path['bbox'],'planned_bbox':list(area),'content_stream_sha256':hashlib.sha256(stream).hexdigest()}


def observe_copy(source_page,target_page,area,*,first_glyph,prose_ids=()):
    source=objects.inventory(source_page);target=objects.inventory(target_page);area=fitz.Rect(area)
    added=target['glyphs'][first_glyph:];prose=set(prose_ids);records=[];issues=[];used=set()
    for g in source['glyphs']:
        if g.get('logical_only') or objects.content_unicode(g).isspace() or g['visibility'] not in {'visible_candidate','partially_clipped'}:continue
        visible=fitz.Rect(g['ink_bbox'])&fitz.Rect(g['clip_bbox'])
        if not (visible&area).get_area():continue
        found=[h for h in added if h['id'] not in used and same_paint(g,h)]
        if len(found)!=1:
            issues.append({'code':'COPIED_SOURCE_PAINT_NOT_UNIQUE','source_id':g['id'],'candidates':[h['id'] for h in found]});continue
        h=found[0];used.add(h['id'])
        if (not fitz.Rect(h['clip_bbox']).contains(visible)
            and not h.get('clip_ink_evidence',{}).get('all_sampled_ink_inside_clip')):
            issues.append({'code':'COPY_INTRODUCES_SOURCE_INK_CLIP','source_id':g['id'],'target_id':h['id'],
                'source_visible_ink_bbox':list(visible),'target_clip_bbox':h['clip_bbox']})
        if g['id'] in prose:
            if (h['visibility']!='visible_candidate' and not (h['visibility']=='partially_clipped'
                and h.get('clip_ink_evidence',{}).get('all_sampled_ink_inside_clip'))):
                issues.append({'code':'COPIED_NEW_PROSE_INK_UNSAFE','source_id':g['id'],'target_id':h['id']})
        records.append({'source_scratch_glyph_id':g['id'],'target_id_at_write':h['id'],
            'role':'new_prose' if g['id'] in prose else 'source_paint_preserved',
            'source_visibility':g['visibility'],'target_descriptor':descriptor(h)})
    expected={g['id'] for g in source['glyphs'] if g['id'] in prose and not g.get('logical_only') and not objects.content_unicode(g).isspace()}
    assigned={r['source_scratch_glyph_id'] for r in records if r['role']=='new_prose'}
    if expected!=assigned:issues.append({'code':'COPIED_NEW_PROSE_COVERAGE_INCOMPLETE','unmapped':sorted(expected-assigned)})
    return {'version':VERSION,'passed':not issues,'issues':issues,'glyph_links':records,
        'source_graphics_roles':'unresolved','coverage_waiver':False}


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def bind_original(copy_record,original):
    """Link copied glyph paints to unique native original glyphs.

    Does not assign formula meaning or classify copied vector/raster content.
    """
    result=json.loads(json.dumps(copy_record));used=set()
    for row in result['glyph_links']:
        if row['role']!='source_paint_preserved':continue
        expected=row['target_descriptor']
        found=[g for g in original['glyphs'] if not g.get('logical_only') and g['id'] not in used
            and g['visibility'] in {'visible_candidate','partially_clipped'}
            and not g['clip_uncertain'] and not g['group_uncertain'] and same_paint(g,expected)]
        if len(found)!=1:raise ValueError('COPIED_ORIGINAL_NATIVE_IDENTITY_AMBIGUOUS')
        g=found[0];used.add(g['id'])
        row['original_source_glyph_id']=g['id'];row['original_source_descriptor']=descriptor(g)
        row['position_delta_pt']=[y-x for x,y in zip(g['origin'],expected['origin'])]
    result['position_rounding_limit_pt']=POSITION_ROUNDING_PT
    return result


def preflight(output):
    """Exercise the actual pending-file and hard-link layout before a call."""
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('LINEAGE_OUTPUT_ALREADY_EXISTS')
    pending=output.with_name('.'+output.name+'.pending-'+uuid.uuid4().hex)
    link=output.parent/('.lineage-probe-'+uuid.uuid4().hex)
    try:
        with pending.open('xb') as stream:stream.write(b'lineage-preflight');stream.flush();os.fsync(stream.fileno())
        os.link(pending,link)
        if link.read_bytes()!=b'lineage-preflight':raise OSError('readback mismatch')
    except OSError as error:raise ValueError('FINAL_WRITER_DURABLE_PATH_UNSUPPORTED') from error
    finally:
        if link.exists():link.unlink()
        if pending.exists():pending.unlink()


def _bound_frames(source_path,target_path,frames):
    source_path=Path(source_path);target_path=Path(target_path)
    if not isinstance(frames,list) or not frames:raise ValueError('LINEAGE_EMPTY_FRAMES')
    before=[file_sha(p) for p in (source_path,target_path)]
    with fitz.open(source_path) as a,fitz.open(target_path) as b:
        data=[];cached={};targets={}
        for frame in frames:
            if (frame.get('producer')!='source_repair.restore_region' or frame.get('producer_code_sha256')!=file_sha(Path(__file__).with_name('source_repair.py'))
                or frame.get('copy',{}).get('passed') is not True or frame['copy'].get('issues')):raise ValueError('LINEAGE_PRODUCER_OR_COPY_UNVERIFIED')
            sp,tp=frame['source_page'],frame['target_page']
            if not 1<=sp<=len(a) or not 1<=tp<=len(b):raise ValueError('LINEAGE_PAGE_BINDING_CHANGED')
            if sp not in cached:cached[sp]=objects.inventory(a[sp-1])
            if objects.digest(cached[sp])!=frame['original_source_native_sha256']:raise ValueError('LINEAGE_SOURCE_NATIVE_CHANGED')
            if tp not in targets:targets[tp]=objects.inventory(b[tp-1])
            target=targets[tp];by_path={r['id']:r for r in target['vector_paths']}
            cover=frame['opaque_cover'];actual=by_path.get(cover['vector_id'])
            if not actual or not actual['native_opaque_rectangle'] or actual['geometry_sha256']!=cover['geometry_sha256']:raise ValueError('LINEAGE_OWNED_COVER_CHANGED')
            links=[];used=set()
            for row in frame['copy']['glyph_links']:
                expected=row['target_descriptor']
                if row['role']=='source_paint_preserved':
                    original={g['id']:g for g in cached[sp]['glyphs']}.get(row.get('original_source_glyph_id'))
                    if (original is None or descriptor(original)!=row.get('original_source_descriptor')
                        or not same_paint(original,expected)):raise ValueError('LINEAGE_ORIGINAL_NATIVE_BINDING_CHANGED')
                found=[g for g in target['glyphs'] if g['id'] not in used and same_paint(expected,g)
                    and g['clip_bbox']==expected['clip_bbox'] and g['visibility']==expected['visibility']]
                if len(found)!=1:raise ValueError('LINEAGE_FINAL_NATIVE_PAINT_CHANGED')
                used.add(found[0]['id']);links.append({**row,'final_target_id':found[0]['id']})
            data.append({**frame,'copy':{**frame['copy'],'glyph_links':links}})
    if before!=[file_sha(p) for p in (source_path,target_path)]:raise ValueError('LINEAGE_ARTIFACT_CHANGED')
    return before,data


def seal(source_path,target_path,frames,output):
    """Recheck and record actual saved hashes and native paint identities.

    No source graphic roles, semantic adjudication or delivery are authorized.
    """
    output=Path(output);before,data=_bound_frames(source_path,target_path,frames)
    result={'version':VERSION,'source_sha256':before[0],'target_sha256':before[1],'frames':data,
        'source_graphics_roles':'unresolved','delivery_authorized':False,'controller_trust':'Local producer and evidence directory must be trusted; hashes are not signatures.'}
    raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    if len(raw)>LIMIT:raise ValueError('LINEAGE_OUTPUT_LIMIT')
    output.parent.mkdir(parents=True,exist_ok=True)
    pending=output.with_name('.'+output.name+'.pending-'+uuid.uuid4().hex)
    with pending.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    # A hard link publishes immutable evidence without replacing prior bytes.
    os.link(pending,output);pending.unlink()
    return result


def verify(path,source_path,target_path):
    path=Path(path)
    if path.is_symlink():raise ValueError('LINEAGE_FILE_LINK_UNSUPPORTED')
    with path.open('rb') as stream:raw=stream.read(LIMIT+1)
    if len(raw)>LIMIT:raise ValueError('LINEAGE_OUTPUT_LIMIT')
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('LINEAGE_DUPLICATE_KEY')
            result[k]=v
        return result
    body=json.loads(raw.decode('utf-8'),object_pairs_hook=unique)
    if (body.get('version')!=VERSION or body.get('delivery_authorized') is not False
        or body.get('source_graphics_roles')!='unresolved'):raise ValueError('INVALID_LINEAGE_RECORD')
    before,data=_bound_frames(source_path,target_path,body['frames'])
    if (before!=[body.get('source_sha256'),body.get('target_sha256')] or data!=body['frames']):raise ValueError('LINEAGE_FINAL_BINDING_CHANGED')
    return body
