#!/usr/bin/env python3
"""
Трекер изменений Яндекс.Директ v3 — BULK + Snapshots

Процесс:
  1. Changes API check → точные ID изменённых кампаний/групп/объявлений
  2. BULK выгрузка всех данных (батч по 10 CampaignIds)
  3. Загрузка предыдущего снимка (если есть) → вычисление диффов
  4. Сохранение текущего состояния как новый снимок
  5. Статистика: Reports API — до и после даты снимка
  6. HTML: карточки изменений (было→стало) + дерево текущего состояния

Выход: data/changes_report_{date}.html + data/snapshots/latest.json
"""
import argparse, hashlib, json, os, sys, time, datetime
import urllib.request, urllib.error
from dataclasses import asdict
from pathlib import Path

from check_access_paths import (
    DirectAccess,
    PageManifest,
    PageResult,
    atomic_write_json,
    fetch_direct_pages,
    fetch_direct_report,
    load_direct_access,
)

API_V5 = "https://api.direct.yandex.com/json/v5"
API_V501 = "https://api.direct.yandex.com/json/v501"
GOAL_ID = os.environ.get("YANDEX_DIRECT_GOAL_ID", "")

STATUS_RU = {
    "ACCEPTED": "Принято", "DRAFT": "Черновик", "MODERATION": "На модерации",
    "PREACCEPTED": "Допущено", "REJECTED": "Отклонено", "ARCHIVED": "Архив",
    "ENDED": "Завершена", "ON": "Включена", "OFF": "Выключена",
    "SUSPENDED": "Остановлена", "SERVING": "Показывается", "ELIGIBLE": "Допущено",
}
FIELD_LABELS = {
    "Name": "Название", "Status": "Статус", "State": "Состояние",
    "DailyBudget": "Дневной бюджет", "NegativeKeywords": "Минус-слова",
    "Title": "Заголовок 1", "Title2": "Заголовок 2", "Text": "Текст",
    "Href": "Ссылка", "DisplayUrlPath": "Отображаемый URL",
    "AdImageHash": "Изображение", "Mobile": "Мобильное",
    "Keyword": "Ключевая фраза", "RegionIds": "Регионы",
}


# ==================== API HELPERS ====================

def api_call(endpoint, method, params, token, login, version="v5", environment="production"):
    host = "api-sandbox.direct.yandex.com" if environment == "sandbox" else "api.direct.yandex.com"
    base = f"https://{host}/json/{version}"
    url = f"{base}/{endpoint}"
    body = json.dumps({"method": method, "params": params}).encode()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept-Language": "ru",
    }
    if login:
        headers["Client-Login"] = login
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  API ERROR {e.code}: {err[:300]}", file=sys.stderr, flush=True)
        return None


def parse_tsv(tsv_text):
    if not tsv_text:
        return []
    lines = tsv_text.strip().split("\n")
    if len(lines) < 2:
        return []
    header = lines[0].split("\t")
    return [{header[i]: (vals[i] if i < len(vals) else "") for i in range(len(header))}
            for vals in (l.split("\t") for l in lines[1:])]


def fetch_paginated(endpoint, method, params, result_key, token, login, version="v5", environment="production"):
    if method != "get":
        raise RuntimeError("Трекер изменений допускает только чтение get")
    access = DirectAccess(token=token, client_login=login, environment=environment)

    def requester(_access, service, page):
        payload = api_call(service, "get", page, token, login, version, environment)
        if not payload:
            raise RuntimeError(f"Неполный ответ {service}.get")
        if payload.get("error"):
            raise RuntimeError(f"Ошибка чтения {service}.get")
        if "result" not in payload:
            raise RuntimeError(f"Нет результата {service}.get")
        return payload

    return fetch_direct_pages(
        access,
        endpoint,
        params,
        result_key,
        version=version,
        requester=requester,
    )


def fetch_batched(endpoint, method, params_fn, result_key, cids, batch_size, token, login, version="v5", environment="production"):
    all_items = []
    pages = 0
    complete = True
    error = ""
    for i in range(0, len(cids), batch_size):
        batch = cids[i:i+batch_size]
        params = params_fn(batch)
        result = fetch_paginated(endpoint, method, params, result_key, token, login, version, environment)
        pages += result.manifest.pages
        all_items.extend(result.rows)
        if not result.manifest.complete:
            complete = False
            error = result.manifest.error
            break
        time.sleep(0.3)
    checksum = hashlib.sha256(
        json.dumps(all_items, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return PageResult(
        rows=all_items,
        manifest=PageManifest(endpoint, result_key, pages, len(all_items), complete, checksum, error),
    )


def require_complete(result, name, manifest_path, sources):
    sources[name] = asdict(result.manifest)
    complete = all(bool(item.get("complete")) for item in sources.values())
    checksum = hashlib.sha256(
        json.dumps(sources, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    atomic_write_json(manifest_path, {"complete": complete, "sources": sources, "checksum": checksum})
    if not result.manifest.complete:
        raise RuntimeError(f"Неполная выгрузка {name}: {result.manifest.error}")
    return result.rows


def completed_result(service, result_key, rows, pages=1):
    serializable = list(rows)
    checksum = hashlib.sha256(
        json.dumps(serializable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return PageResult(
        rows=serializable,
        manifest=PageManifest(service, result_key, pages, len(serializable), True, checksum),
    )


def fetch_modified_ids(token, login, cids, days, environment="production"):
    """Changes API: checkCampaigns + check → точные ID изменённых сущностей."""
    ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    mod_camps, mod_groups, mod_ads = set(), set(), set()
    pages = 1

    r1 = api_call("changes", "checkCampaigns", {"Timestamp": ts}, token, login, environment=environment)
    if not r1 or "result" not in r1:
        raise RuntimeError("Changes API не вернул полный список кампаний")

    our_cids = set(cids)
    children_cids = []
    for c in r1["result"].get("Campaigns", []):
        cid = c.get("CampaignId")
        if cid not in our_cids:
            continue
        changes_in = set(c.get("ChangesIn", []))
        if "SELF" in changes_in:
            mod_camps.add(cid)
        if "CHILDREN" in changes_in:
            children_cids.append(cid)

    # Точные ID групп/объявлений через check (до 3000 за раз)
    for i in range(0, len(children_cids), 3000):
        pages += 1
        batch = children_cids[i:i + 3000]
        r2 = api_call("changes", "check", {
            "CampaignIds": batch,
            "FieldNames": ["AdGroupIds", "AdIds"],
            "Timestamp": ts,
        }, token, login, environment=environment)
        if not r2 or "result" not in r2:
            raise RuntimeError("Changes API не вернул полный список изменённых объектов")
        mod = r2["result"].get("Modified", {})
        mod_groups.update(mod.get("AdGroupIds", []))
        mod_ads.update(mod.get("AdIds", []))
        time.sleep(0.5)

    return mod_camps, mod_groups, mod_ads, pages


def get_report_bulk(report_type, fields, date_from, date_to, token, login, output_dir, name="", with_goals=True, environment="production"):
    report_name = f"ct3_{report_type}_{name}_{int(time.time())}"
    params = {
        "SelectionCriteria": {"DateFrom": date_from, "DateTo": date_to},
        "FieldNames": fields, "ReportName": report_name,
        "ReportType": report_type, "DateRangeType": "CUSTOM_DATE",
        "Format": "TSV", "IncludeVAT": "YES", "IncludeDiscount": "NO",
    }
    if with_goals and GOAL_ID:
        params["Goals"] = [GOAL_ID]
        params["AttributionModels"] = ["LC"]
    access = DirectAccess(token=token, client_login=login, environment=environment)
    state = fetch_direct_report(access, params, Path(output_dir))
    if state.get("http_status") == 400 and with_goals:
        return get_report_bulk(report_type, fields, date_from, date_to, token, login, output_dir, name + "_ng", with_goals=False, environment=environment)
    if state.get("status") != "ready":
        raise RuntimeError(f"Reports API не подготовил отчёт: {state.get('status')}")
    return Path(state["artifact_path"]).read_text(encoding="utf-8")


def fetch_image_urls(token, login, hashes, environment="production"):
    if not hashes:
        return {}
    url_map = {}
    for i in range(0, len(hashes), 50):
        batch = hashes[i:i + 50]
        r = api_call("adimages", "get", {
            "SelectionCriteria": {"AdImageHashes": batch},
            "FieldNames": ["AdImageHash", "OriginalUrl"],
        }, token, login, environment=environment)
        time.sleep(0.3)
        if not r or "result" not in r:
            raise RuntimeError("Неполная выгрузка изображений")
        for img in r["result"].get("AdImages", []):
            url_map[img["AdImageHash"]] = img.get("OriginalUrl", "")
    return url_map


def parse_perf_row(r):
    def num(k): return float(r.get(k, "0").replace("--", "0"))
    return {"impressions": int(num("Impressions")), "clicks": int(num("Clicks")),
            "cost": num("Cost"), "ctr": num("Ctr"), "avg_cpc": num("AvgCpc") if "AvgCpc" in r else 0,
            "conversions": num("Conversions"), "cpa": num("CostPerConversion"),
            "cr": num("ConversionRate") if "ConversionRate" in r else 0,
            "bounce_rate": num("BounceRate") if "BounceRate" in r else 0}


# ==================== SNAPSHOT ====================

def extract_neg(obj):
    nk = obj.get("NegativeKeywords")
    if isinstance(nk, dict):
        return sorted(nk.get("Items", []))
    if isinstance(nk, list):
        return sorted(nk)
    return []


def build_snapshot(all_camps, all_groups, all_ads, all_keywords):
    snap = {"campaigns": {}, "groups": {}, "ads": {}, "keywords": {}}
    for c in all_camps:
        b = c.get("DailyBudget", {})
        snap["campaigns"][str(c["Id"])] = {
            "Name": c.get("Name", ""), "Status": c.get("Status", ""),
            "State": c.get("State", ""), "NegativeKeywords": extract_neg(c),
            "BudgetAmount": int(b.get("Amount", 0)) // 1000000 if b else 0,
        }
    for g in all_groups:
        rids = g.get("RegionIds")
        if isinstance(rids, dict):
            rids = rids.get("Items", [])
        elif not isinstance(rids, list):
            rids = []
        snap["groups"][str(g["Id"])] = {
            "Name": g.get("Name", ""), "Status": g.get("Status", ""),
            "CampaignId": g.get("CampaignId"), "NegativeKeywords": extract_neg(g),
            "RegionIds": sorted(rids),
        }
    for a in all_ads:
        ta = a.get("TextAd", {})
        snap["ads"][str(a["Id"])] = {
            "AdGroupId": a.get("AdGroupId"), "CampaignId": a.get("CampaignId"),
            "Status": a.get("Status", ""), "Title": ta.get("Title", ""),
            "Title2": ta.get("Title2", ""), "Text": ta.get("Text", ""),
            "Href": ta.get("Href", ""), "DisplayUrlPath": ta.get("DisplayUrlPath", ""),
            "AdImageHash": ta.get("AdImageHash", ""), "Mobile": ta.get("Mobile", "NO"),
            "SitelinkSetId": ta.get("SitelinkSetId"),
        }
    for k in all_keywords:
        snap["keywords"][str(k["Id"])] = {
            "Keyword": k.get("Keyword", ""), "AdGroupId": k.get("AdGroupId"),
            "Status": k.get("Status", ""), "State": k.get("State", ""),
        }
    return snap


def save_snapshot(data_dir, snap, retention_days=90):
    snap["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    snap_dir = os.path.join(data_dir, "snapshots")
    os.makedirs(snap_dir, exist_ok=True)
    # Бэкап предыдущего latest.json с таймстампом
    latest_path = os.path.join(snap_dir, "latest.json")
    if os.path.exists(latest_path):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(snap_dir, f"snap_{ts}.json")
        os.rename(latest_path, backup_path)
    # Сохраняем новый
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False)
    os.chmod(latest_path, 0o600)
    cutoff = time.time() - max(1, retention_days) * 86400
    for name in os.listdir(snap_dir):
        candidate = os.path.join(snap_dir, name)
        if name.startswith("snap_") and name.endswith(".json") and os.path.getmtime(candidate) < cutoff:
            os.unlink(candidate)
    return latest_path


def load_snapshot(data_dir):
    path = os.path.join(data_dir, "snapshots", "latest.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================== DIFF ENGINE ====================

def fmt_val(field, val):
    if field in ("Status", "State"):
        return STATUS_RU.get(val, val) if val else "—"
    if field == "BudgetAmount":
        return f"{val} руб/день" if val else "не задан"
    if field == "Mobile":
        return "Да" if val == "YES" else "Нет"
    if field == "NegativeKeywords":
        return f"{len(val)} слов" if val else "нет"
    if field == "RegionIds":
        return ", ".join(str(r) for r in (val or []))[:80] or "—"
    if field == "SitelinkSetId":
        return str(val) if val else "нет"
    if field == "AdImageHash":
        return str(val)[:12] + "..." if val else "нет"
    if not val:
        return "—"
    return str(val)


def normalize_val(field, val):
    """Нормализует значение для корректного сравнения (None → пустое значение)."""
    if field in ("NegativeKeywords", "RegionIds"):
        return sorted(val) if val else []
    if field in ("SitelinkSetId", "AdImageHash"):
        return val if val else None
    if field in ("Title2", "DisplayUrlPath", "Href"):
        return val if val else ""
    return val


def diff_entity(old, new, fields):
    """Сравнивает поля двух снимков сущности → список изменений."""
    diffs = []
    for f in fields:
        # Пропускаем поле если его НЕ БЫЛО в предыдущем снимке (миграция схемы)
        if f not in old:
            continue
        o, n = normalize_val(f, old.get(f)), normalize_val(f, new.get(f))
        if f == "NegativeKeywords":
            old_set, new_set = set(o or []), set(n or [])
            if old_set != new_set:
                added = sorted(new_set - old_set)
                removed = sorted(old_set - new_set)
                diffs.append({"field": f, "old": old.get(f), "new": new.get(f), "neg_added": added, "neg_removed": removed})
        elif o != n:
            if f == "AdImageHash":
                # Храним RAW хеш для поиска URL, НЕ обрезанный
                diffs.append({"field": f, "old": old.get(f) or "", "new": new.get(f) or ""})
            else:
                diffs.append({"field": f, "old": fmt_val(f, old.get(f)), "new": fmt_val(f, new.get(f))})
    return diffs


def compute_all_diffs(cur_snap, prev_snap, mod_camps, mod_groups, mod_ads, camps_by_id, groups_by_id, filtered_cids=None):
    """Вычисляет все изменения: current vs snapshot.
    filtered_cids: если задан (set of int) — при проверке 'deleted' игнорируем сущности
    из кампаний, не входящих в фильтр (иначе partial scan = ложные 'deleted').
    """
    changes = []

    camp_fields = ["Name", "Status", "State", "BudgetAmount", "NegativeKeywords"]
    group_fields = ["Name", "Status", "RegionIds", "NegativeKeywords"]
    ad_fields = ["Status", "Title", "Title2", "Text", "Href", "DisplayUrlPath", "AdImageHash", "Mobile", "SitelinkSetId"]
    kw_fields = ["Keyword", "Status", "State"]

    # Кампании — сравниваем ВСЕ, не только помеченные Changes API
    for cid_s, cur in cur_snap["campaigns"].items():
        prev = prev_snap["campaigns"].get(cid_s)
        cname = cur.get("Name", f"#{cid_s}")
        if prev is None:
            changes.append({"type": "campaign", "id": int(cid_s), "name": cname,
                            "action": "added", "diffs": [], "campaign_name": cname})
            continue
        diffs = diff_entity(prev, cur, camp_fields)
        if diffs:
            changes.append({"type": "campaign", "id": int(cid_s), "name": cname,
                            "action": "modified", "diffs": diffs, "campaign_name": cname})
    for cid_s, prev in prev_snap["campaigns"].items():
        if cid_s not in cur_snap["campaigns"]:
            # Если partial scan — не считаем deleted кампании вне фильтра
            if filtered_cids and int(cid_s) not in filtered_cids:
                continue
            changes.append({"type": "campaign", "id": int(cid_s), "name": prev.get("Name", "?"),
                            "action": "deleted", "diffs": [], "campaign_name": prev.get("Name", "?")})

    # Группы
    for gid_s, cur in cur_snap["groups"].items():
        prev = prev_snap["groups"].get(gid_s)
        cid = cur.get("CampaignId")
        cname = camps_by_id.get(cid, {}).get("Name", f"#{cid}")
        gname = cur.get("Name", f"#{gid_s}")
        if prev is None:
            changes.append({"type": "group", "id": int(gid_s), "name": gname,
                            "action": "added", "diffs": [], "campaign_name": cname, "campaign_id": cid})
            continue
        diffs = diff_entity(prev, cur, group_fields)
        if diffs:
            changes.append({"type": "group", "id": int(gid_s), "name": gname,
                            "action": "modified", "diffs": diffs, "campaign_name": cname, "campaign_id": cid})
    for gid_s, prev in prev_snap["groups"].items():
        if gid_s not in cur_snap["groups"]:
            cid = prev.get("CampaignId")
            if filtered_cids and cid and cid not in filtered_cids:
                continue
            changes.append({"type": "group", "id": int(gid_s), "name": prev.get("Name", "?"),
                            "action": "deleted", "diffs": [], "campaign_name": camps_by_id.get(cid, {}).get("Name", "?"), "campaign_id": cid})

    # Объявления
    for aid_s, cur in cur_snap["ads"].items():
        prev = prev_snap["ads"].get(aid_s)
        cid = cur.get("CampaignId")
        gid = cur.get("AdGroupId")
        cname = camps_by_id.get(cid, {}).get("Name", f"#{cid}")
        gname = groups_by_id.get(gid, {}).get("Name", f"#{gid}")
        if prev is None:
            changes.append({"type": "ad", "id": int(aid_s), "name": cur.get("Title", "?"),
                            "action": "added", "diffs": [], "campaign_name": cname, "group_name": gname, "campaign_id": cid})
            continue
        diffs = diff_entity(prev, cur, ad_fields)
        if diffs:
            changes.append({"type": "ad", "id": int(aid_s), "name": cur.get("Title", "?"),
                            "action": "modified", "diffs": diffs, "campaign_name": cname, "group_name": gname, "campaign_id": cid})
    for aid_s, prev in prev_snap["ads"].items():
        if aid_s not in cur_snap["ads"]:
            cid = prev.get("CampaignId")
            if filtered_cids and cid and cid not in filtered_cids:
                continue
            changes.append({"type": "ad", "id": int(aid_s), "name": prev.get("Title", "?"),
                            "action": "deleted", "diffs": [], "campaign_name": camps_by_id.get(cid, {}).get("Name", "?"), "campaign_id": cid})

    # Ключевые слова
    for kid_s, cur in cur_snap["keywords"].items():
        prev = prev_snap["keywords"].get(kid_s)
        gid = cur.get("AdGroupId")
        ginfo = groups_by_id.get(gid, {})
        cid = ginfo.get("CampaignId")
        cname = camps_by_id.get(cid, {}).get("Name", f"#{cid}")
        if prev is None:
            changes.append({"type": "keyword", "id": int(kid_s), "name": cur.get("Keyword", "?"),
                            "action": "added", "diffs": [], "campaign_name": cname, "campaign_id": cid})
            continue
        diffs = diff_entity(prev, cur, kw_fields)
        if diffs:
            changes.append({"type": "keyword", "id": int(kid_s), "name": cur.get("Keyword", "?"),
                            "action": "modified", "diffs": diffs, "campaign_name": cname, "campaign_id": cid})
    for kid_s, prev in prev_snap["keywords"].items():
        if kid_s not in cur_snap["keywords"]:
            # Определяем кампанию ключа через группу из prev_snap
            gid = prev.get("AdGroupId")
            prev_grp = prev_snap["groups"].get(str(gid), {}) if gid else {}
            cid = prev_grp.get("CampaignId")
            if filtered_cids and cid and cid not in filtered_cids:
                continue
            changes.append({"type": "keyword", "id": int(kid_s), "name": prev.get("Keyword", "?"),
                            "action": "deleted", "diffs": [], "campaign_name": "?", "campaign_id": cid})

    return changes


# ==================== HTML ====================

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

TYPE_LABELS = {"campaign": "Кампания", "group": "Группа", "ad": "Объявление", "keyword": "Ключ"}
ACTION_LABELS = {"added": "ДОБАВЛЕНО", "modified": "ИЗМЕНЕНО", "deleted": "УДАЛЕНО"}
ACTION_COLORS = {"added": "#1a8c4e", "modified": "#e65100", "deleted": "#c62828"}


def render_change_card(ch, login, img_urls=None):
    action = ch["action"]
    color = ACTION_COLORS[action]
    type_label = TYPE_LABELS.get(ch["type"], ch["type"])
    action_label = ACTION_LABELS[action]

    # Breadcrumb: Кампания > Группа > Объявление
    breadcrumb = esc(ch.get("campaign_name", ""))
    if ch.get("group_name"):
        breadcrumb += f' <span style="color:#ccc">›</span> {esc(ch["group_name"])}'

    # Link to Direct
    cid = ch.get("campaign_id") or ch.get("id")
    link = f'https://direct.yandex.ru/dna/grid?ulogin={login}&cmd=showCamp&cid={cid}' if cid else ""

    html = f'''<div class="ch-card" style="border-left:4px solid {color}" data-type="{ch["type"]}" data-action="{action}" data-camp="{esc(ch.get("campaign_name",""))}">
  <div class="ch-head">
    <div>
      <span class="ch-badge" style="background:{color}15;color:{color}">{action_label}</span>
      <span class="ch-type">{type_label}</span>
      <span class="ch-name">{esc(ch["name"])}</span>
      <span class="ch-id">#{ch["id"]}</span>
    </div>
    <div class="ch-breadcrumb">{breadcrumb}'''
    if link:
        html += f' <a href="{link}" target="_blank" class="ch-link">↗</a>'
    html += '</div></div>'

    # Diffs
    if ch["diffs"]:
        html += '<div class="ch-diffs">'
        for d in ch["diffs"]:
            field = FIELD_LABELS.get(d["field"], d["field"])
            if d["field"] == "NegativeKeywords":
                html += f'<div class="ch-diff-row"><span class="ch-field">{esc(field)}:</span><div>'
                for w in d.get("neg_added", []):
                    html += f'<span class="neg-add">+{esc(w)}</span> '
                for w in d.get("neg_removed", []):
                    html += f'<span class="neg-rem">-{esc(w)}</span> '
                old_count = len(d.get("old") or [])
                new_count = len(d.get("new") or [])
                html += f'<span class="ch-count">({old_count} → {new_count})</span>'
                html += '</div></div>'
            elif d["field"] == "AdImageHash" and img_urls:
                old_url = img_urls.get(d["old"], "") if d["old"] else ""
                new_url = img_urls.get(d["new"], "") if d["new"] else ""
                html += f'<div class="ch-diff-row"><span class="ch-field">{esc(field)}:</span>'
                html += '<div style="display:flex;gap:16px;align-items:flex-start;margin-top:8px">'
                # БЫЛО
                html += '<div style="text-align:center">'
                html += '<div style="font-size:11px;font-weight:700;color:#c62828;margin-bottom:4px">БЫЛО</div>'
                if old_url:
                    html += f'<img src="{esc(old_url)}" style="width:150px;height:150px;object-fit:cover;border-radius:8px;border:3px solid #ef9a9a">'
                elif d["old"]:
                    html += f'<span class="ch-old">{esc(str(d["old"])[:16])}</span>'
                else:
                    html += '<span class="ch-old">нет</span>'
                html += '</div>'
                html += '<span class="ch-arrow" style="margin-top:60px">→</span>'
                # СТАЛО
                html += '<div style="text-align:center">'
                html += '<div style="font-size:11px;font-weight:700;color:#1a8c4e;margin-bottom:4px">СТАЛО</div>'
                if new_url:
                    html += f'<img src="{esc(new_url)}" style="width:150px;height:150px;object-fit:cover;border-radius:8px;border:3px solid #81c784">'
                elif d["new"]:
                    html += f'<span class="ch-new">{esc(str(d["new"])[:16])}</span>'
                else:
                    html += '<span class="ch-new">нет</span>'
                html += '</div></div></div>'
            else:
                html += f'<div class="ch-diff-row"><span class="ch-field">{esc(field)}:</span>'
                html += f'<span class="ch-old">{esc(str(d["old"]))}</span>'
                html += f'<span class="ch-arrow">→</span>'
                html += f'<span class="ch-new">{esc(str(d["new"]))}</span></div>'
        html += '</div>'
    elif action == "added":
        html += '<div class="ch-diffs"><div class="ch-diff-row" style="color:#1a8c4e">Новая сущность добавлена</div></div>'
    elif action == "deleted":
        html += '<div class="ch-diffs"><div class="ch-diff-row" style="color:#c62828">Сущность удалена</div></div>'

    html += '</div>'
    return html


def render_perf_table(before, after, label_before, label_after):
    metrics = [
        ("Показы", "impressions", "d", ""), ("Клики", "clicks", "d", ""),
        ("CTR", "ctr", ".2f", "%"), ("Расход", "cost", ",.0f", " р"),
        ("CPC", "avg_cpc", ".1f", " р"), ("Конверсии", "conversions", ".0f", ""),
        ("CPA", "cpa", ",.0f", " р"), ("CR", "cr", ".2f", "%"),
    ]
    positive_up = {"impressions", "clicks", "ctr", "conversions", "cr"}
    positive_down = {"cost", "avg_cpc", "cpa"}

    html = f'<div class="perf"><h3>Статистика: {esc(label_before)} vs {esc(label_after)}</h3><table>'
    html += f'<tr><th>Метрика</th><th>{esc(label_before)}</th><th>{esc(label_after)}</th><th>Дельта</th></tr>'
    for label, key, fmt, suf in metrics:
        b, a = before.get(key, 0), after.get(key, 0)
        delta = a - b
        sign = "+" if delta > 0 else ""
        if abs(delta) < 0.01:
            style = "color:#ccc"
        elif (key in positive_up and delta > 0) or (key in positive_down and delta < 0):
            style = "color:#1a8c4e;font-weight:600"
        elif (key in positive_up and delta < 0) or (key in positive_down and delta > 0):
            style = "color:#c62828;font-weight:600"
        else:
            style = "color:#666"
        html += f'<tr><td>{label}</td><td>{format(b, fmt)}{suf}</td><td>{format(a, fmt)}{suf}</td>'
        html += f'<td style="{style}">{sign}{format(delta, fmt)}{suf}</td></tr>'
    html += '</table></div>'
    return html


def generate_html(all_changes, campaigns_data, report_date, days, snap_date, login,
                  camp_perf_before, camp_perf_after, label_before, label_after, img_urls):
    n_changes = len(all_changes)
    n_camps_affected = len(set(ch.get("campaign_name", "") for ch in all_changes))
    n_camps = len(campaigns_data)
    total_groups = sum(len(cd["groups"]) for cd in campaigns_data)
    total_ads = sum(len(cd["ads"]) for cd in campaigns_data)

    by_type = {}
    for ch in all_changes:
        by_type.setdefault(ch["type"], []).append(ch)

    snap_info = f"Снимок от: {snap_date[:10]}" if snap_date else "Первый запуск — снимок сохранён"

    html = f'''<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Трекер изменений — {report_date}</title>
<style>
:root {{ --bg:#f5f7fa; --card:#fff; --border:#e8ecf1; --text:#1a1a2e; --muted:#888 }}
* {{ margin:0;padding:0;box-sizing:border-box }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.5 }}
.w {{ max-width:1200px;margin:0 auto;padding:20px }}
.hdr {{ background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:24px 28px;border-radius:16px;margin-bottom:20px }}
.hdr h1 {{ font-size:22px;font-weight:700;margin-bottom:4px }}
.hdr .m {{ font-size:13px;opacity:.7 }}
.cards {{ display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px }}
.card {{ background:var(--card);border-radius:12px;padding:16px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06) }}
.card .n {{ font-size:28px;font-weight:800 }}
.card .l {{ font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px }}

/* Sections */

/* Filter */
.flt {{ display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px;padding:8px 0 }}
.flt select,.flt input {{ padding:6px 10px;border:1px solid var(--border);border-radius:6px;font-size:13px }}
.flt input {{ width:200px }}
.flt label {{ font-size:12px;font-weight:600;color:var(--muted) }}

/* Change cards — ЯРКИЕ, ЗАМЕТНЫЕ */
.ch-card {{ background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,.08);border-left:5px solid #e65100;position:relative }}
.ch-card::before {{ content:'';position:absolute;top:0;left:-5px;bottom:0;width:5px;border-radius:12px 0 0 12px }}
.ch-head {{ display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:12px }}
.ch-badge {{ padding:4px 12px;border-radius:6px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.5px }}
.ch-type {{ font-size:13px;color:var(--muted);margin:0 6px;font-weight:600 }}
.ch-name {{ font-weight:700;font-size:16px }}
.ch-id {{ font-size:12px;color:var(--muted) }}
.ch-breadcrumb {{ font-size:12px;color:var(--muted) }}
.ch-link {{ color:#1565c0;text-decoration:none;font-weight:700;font-size:14px }}
.ch-diffs {{ background:linear-gradient(135deg,#fafbfc,#f0f4f8);border-radius:10px;padding:14px 18px;border:1px solid var(--border) }}
.ch-diff-row {{ display:flex;align-items:center;gap:12px;padding:6px 0;flex-wrap:wrap }}
.ch-field {{ font-weight:700;font-size:14px;color:#333;min-width:140px }}
.ch-old {{ background:#ffcdd2;color:#b71c1c;padding:4px 10px;border-radius:6px;font-size:14px;text-decoration:line-through;font-weight:500 }}
.ch-new {{ background:#c8e6c9;color:#1b5e20;padding:4px 10px;border-radius:6px;font-size:14px;font-weight:700 }}
.ch-arrow {{ color:#e65100;font-size:18px;font-weight:900 }}
.ch-count {{ font-size:12px;color:var(--muted);font-weight:600 }}
.neg-add {{ background:#c8e6c9;color:#1b5e20;padding:3px 8px;border-radius:4px;font-size:13px;display:inline-block;margin:2px;font-weight:600 }}
.neg-rem {{ background:#ffcdd2;color:#b71c1c;padding:3px 8px;border-radius:4px;font-size:13px;text-decoration:line-through;display:inline-block;margin:2px;font-weight:500 }}
.empty-msg {{ text-align:center;color:var(--muted);padding:40px;font-size:16px }}
.changes-section {{ background:#fff8e1;border:2px solid #ffe082;border-radius:14px;padding:20px;margin-bottom:24px }}
.changes-section h2 {{ font-size:18px;font-weight:800;color:#e65100;margin-bottom:14px }}

/* Perf table */
.perf {{ margin:16px 0;border-top:1px solid var(--border);padding-top:12px }}
.perf h3 {{ font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px }}
.perf table {{ width:100%;border-collapse:collapse;font-size:13px }}
.perf th {{ background:#f8f9fb;padding:6px 10px;text-align:right;font-weight:600;color:#555;border-bottom:2px solid var(--border) }}
.perf td {{ padding:6px 10px;text-align:right;border-bottom:1px solid #f0f2f5 }}
.perf th:first-child,.perf td:first-child {{ text-align:left }}

/* Campaign tree */
.camp {{ background:var(--card);border-radius:12px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow:hidden }}
.camp-h {{ padding:14px 18px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid var(--border);user-select:none }}
.camp-h:hover {{ background:#fafbfc }}
.camp-h h2 {{ font-size:15px;font-weight:600 }}
.camp-b {{ padding:0 }}
.camp-b.hid {{ display:none }}
.grp {{ border-bottom:1px solid var(--border) }}
.grp-h {{ padding:10px 18px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-size:13px }}
.grp-h:hover {{ background:#fafbfc }}
.grp-h .t {{ font-weight:600 }}
.grp-h .info {{ font-size:12px;color:var(--muted) }}
.grp-b {{ padding:0 18px 14px;display:none }}
.grp-b.open {{ display:block }}
.ad {{ background:#f8f9fb;border-radius:8px;padding:12px;margin:6px 0;display:grid;grid-template-columns:auto 1fr;gap:12px }}
.ad-img {{ width:100px;height:100px;border-radius:6px;object-fit:cover;background:#eee }}
.ad-img-none {{ width:100px;height:100px;border-radius:6px;background:#f0f2f5;display:flex;align-items:center;justify-content:center;color:#ccc;font-size:10px }}
.ad-title {{ font-size:15px;font-weight:700;color:#1565c0 }}
.ad-title2 {{ font-size:13px;color:#1a8c4e }}
.ad-text {{ font-size:12px;color:#333;margin:4px 0 }}
.ad-meta {{ font-size:11px;color:var(--muted) }}
.ad-url {{ color:#1a8c4e;font-size:11px }}
.kw {{ display:inline-block;background:#e8f0fe;color:#1565c0;padding:2px 8px;border-radius:4px;font-size:11px;margin:2px }}
.kw-off {{ background:#fce8e8;color:#c62828;text-decoration:line-through }}
.neg {{ display:inline-block;background:#fce8e8;color:#c62828;padding:1px 6px;border-radius:3px;font-size:10px;margin:1px }}
.arrow {{ transition:transform .2s;font-size:13px }}
.collapsed .arrow {{ transform:rotate(-90deg) }}
.sb {{ padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600 }}
.footer {{ text-align:center;color:#bbb;font-size:11px;margin-top:20px }}
</style></head><body>
<div class="w">
<div class="hdr">
  <h1>Трекер изменений рекламных кампаний</h1>
  <div class="m">Период: {days} дн. | {snap_info} | Отчёт: {report_date}</div>
</div>
<div class="cards">
  <div class="card"><div class="n" style="color:#e65100">{n_changes}</div><div class="l">Изменений</div></div>
  <div class="card"><div class="n">{n_camps_affected}</div><div class="l">РК затронуто</div></div>
  <div class="card"><div class="n">{n_camps}</div><div class="l">Всего кампаний</div></div>
  <div class="card"><div class="n">{total_groups}</div><div class="l">Групп</div></div>
  <div class="card"><div class="n">{total_ads}</div><div class="l">Объявлений</div></div>
</div>

'''

    # ===== СЕКЦИЯ: ИЗМЕНЕНИЯ (если есть) =====
    if all_changes:
        html += f'<div class="changes-section">'
        html += f'<h2>Что изменилось с {snap_date[:10] if snap_date else "???"} ({n_changes} изменений)</h2>'
        html += '''<div class="flt">
  <label>Тип:</label>
  <select id="chType" onchange="filterChanges()">
    <option value="">Все</option>
    <option value="campaign">Кампании</option>
    <option value="group">Группы</option>
    <option value="ad">Объявления</option>
    <option value="keyword">Ключи</option>
  </select>
  <label>Действие:</label>
  <select id="chAction" onchange="filterChanges()">
    <option value="">Все</option>
    <option value="modified">Изменено</option>
    <option value="added">Добавлено</option>
    <option value="deleted">Удалено</option>
  </select>
  <input type="text" id="chSearch" placeholder="Поиск..." oninput="filterChanges()">
</div>'''
        by_camp = {}
        for ch in all_changes:
            cn = ch.get("campaign_name", "Без кампании")
            by_camp.setdefault(cn, []).append(ch)
        for cname, chs in sorted(by_camp.items()):
            html += f'<h3 style="font-size:15px;color:#e65100;margin:16px 0 10px;padding-bottom:6px;border-bottom:2px solid #ffe082;font-weight:700">{esc(cname)} ({len(chs)})</h3>'
            for ch in chs:
                html += render_change_card(ch, login, img_urls)
        html += '</div>'
    elif snap_date:
        html += '<div style="background:#e8f5e9;border:2px solid #a5d6a7;border-radius:12px;padding:16px;margin-bottom:20px;text-align:center;font-weight:600;color:#2e7d32">Изменений не обнаружено с {}</div>'.format(snap_date[:10])

    # ===== ДЕРЕВО КАМПАНИЙ (всегда показываем) =====
    html += '''<div class="flt">
  <input type="text" id="stSearch" placeholder="Поиск по кампаниям..." oninput="filterState()">
  <label style="display:flex;align-items:center;gap:4px;cursor:pointer"><input type="checkbox" id="stHideArch" checked onchange="filterState()"> Скрыть архивные</label>
</div>'''

    for cd in campaigns_data:
        camp = cd["campaign"]
        cid = camp["Id"]
        cname = esc(camp.get("Name", f"Campaign {cid}"))
        groups = cd["groups"]
        ads = cd["ads"]
        kws = cd["keywords"]
        grp_perf = cd.get("group_performance", {})
        perf_b = camp_perf_before.get(cid)
        perf_a = camp_perf_after.get(cid)
        neg_kws = extract_neg(camp)

        state = camp.get("State", "?")
        st_color = {"ON": "#1a8c4e", "SUSPENDED": "#c62828", "OFF": "#c62828", "ENDED": "#999", "ARCHIVED": "#999"}.get(state, "#666")
        status = camp.get("Status", "?")
        su_color = {"ACCEPTED": "#1a8c4e", "MODERATION": "#e65100", "DRAFT": "#999", "REJECTED": "#c62828", "ARCHIVED": "#999"}.get(status, "#666")

        budget = camp.get("DailyBudget", {})
        budget_str = f'{int(budget.get("Amount", 0)) // 1000000} руб/день' if budget else "—"

        # Group data structures
        groups_by_id_local = {g["Id"]: g for g in groups}
        ads_by_group = {}
        for a in ads:
            ads_by_group.setdefault(a.get("AdGroupId"), []).append(a)
        kws_by_group = {}
        for k in kws:
            kws_by_group.setdefault(k.get("AdGroupId"), []).append(k)

        n_active = sum(1 for g in groups if g.get("Status") not in ("ARCHIVED",))

        html += f'''
<div class="camp" data-status="{state}">
  <div class="camp-h" onclick="toggleCamp(this)">
    <h2>{cname} <span style="color:#999;font-weight:400;font-size:12px">#{cid}</span>
      <span class="sb" style="background:{st_color}15;color:{st_color}">{STATUS_RU.get(state,state)}</span>
      <span class="sb" style="background:{su_color}15;color:{su_color}">{STATUS_RU.get(status,status)}</span>
    </h2>
    <div><span style="font-size:12px;color:#999">{n_active} гр, {len(ads)} об, {budget_str}</span>
      <a href="https://direct.yandex.ru/dna/grid?ulogin={login}&cmd=showCamp&cid={cid}" target="_blank" style="color:#1565c0;font-size:11px;margin-left:8px">↗</a>
      <span class="arrow">▶</span></div>
  </div>
  <div class="camp-b">'''

        # Performance — показываем даже если есть данные только за 1 период
        if perf_b or perf_a:
            html += render_perf_table(perf_b or {}, perf_a or {}, label_before, label_after)

        # Neg keywords
        if neg_kws:
            html += f'<div style="padding:8px 18px;border-bottom:1px solid var(--border);font-size:12px"><b style="color:var(--muted)">Минус-слова ({len(neg_kws)}):</b> '
            html += " ".join(f'<span class="neg">{esc(w)}</span>' for w in sorted(neg_kws)[:50])
            if len(neg_kws) > 50:
                html += f' <span style="color:var(--muted)">...ещё {len(neg_kws)-50}</span>'
            html += '</div>'

        # Groups sorted by cost
        sorted_groups = sorted(groups, key=lambda g: -(grp_perf.get(g["Id"], {}).get("cost", 0)))
        for g in sorted_groups:
            gid = g["Id"]
            gname = esc(g.get("Name", f"Group {gid}"))
            gstatus = g.get("Status", "?")
            g_ads = ads_by_group.get(gid, [])
            g_kws = kws_by_group.get(gid, [])
            gp = grp_perf.get(gid, {})
            gp_str = f'{gp.get("clicks",0)} кл, {gp.get("cost",0):.0f}р' if gp else ""
            g_neg = extract_neg(g)
            gs_color = {"ACCEPTED": "#1a8c4e", "MODERATION": "#e65100", "DRAFT": "#999", "REJECTED": "#c62828", "ARCHIVED": "#999", "SUSPENDED": "#c62828"}.get(gstatus, "#666")

            html += f'''
    <div class="grp" data-status="{gstatus}" data-text="{esc(gname.lower())}">
      <div class="grp-h" onclick="toggleGrp(this)">
        <div><span class="t">{gname}</span> <span class="sb" style="background:{gs_color}15;color:{gs_color}">{STATUS_RU.get(gstatus,gstatus)}</span>
          <span class="info">{len(g_ads)} об, {len(g_kws)} кл</span></div>
        <div><span class="info">{gp_str}</span> <span class="arrow">▶</span></div>
      </div>
      <div class="grp-b">'''

            if g_neg:
                html += f'<div style="margin-bottom:6px;font-size:11px"><b style="color:var(--muted)">Минус-слова:</b> '
                html += " ".join(f'<span class="neg">{esc(w)}</span>' for w in g_neg)
                html += '</div>'

            if g_kws:
                html += '<div style="margin-bottom:6px">'
                for k in g_kws:
                    cls = "kw-off" if k.get("Status") in ("SUSPENDED", "ARCHIVED") else ""
                    html += f'<span class="kw {cls}">{esc(k.get("Keyword","?"))}</span>'
                html += '</div>'

            for a in g_ads:
                ta = a.get("TextAd", {})
                title = esc(ta.get("Title", "—"))
                title2 = esc(ta.get("Title2", ""))
                text = esc(ta.get("Text", ""))
                href = ta.get("Href", "")
                img_hash = ta.get("AdImageHash", "")
                img_url = img_urls.get(img_hash, "") if img_hash else ""
                astatus = a.get("Status", "?")
                as_color = {"ACCEPTED": "#1a8c4e", "MODERATION": "#e65100", "DRAFT": "#999", "REJECTED": "#c62828", "ARCHIVED": "#999"}.get(astatus, "#666")
                is_mobile = ta.get("Mobile", "NO") == "YES"

                if img_url:
                    img_html = f'<img class="ad-img" src="{esc(img_url)}" loading="lazy">'
                else:
                    img_html = '<div class="ad-img-none">—</div>'

                html += f'''<div class="ad">
          {img_html}
          <div>
            <div class="ad-title">{title}</div>
            {"<div class='ad-title2'>"+title2+"</div>" if title2 else ""}
            <div class="ad-text">{text}</div>
            <div class="ad-meta">#{a["Id"]} <span class="sb" style="background:{as_color}15;color:{as_color}">{STATUS_RU.get(astatus,astatus)}</span>{"<span class='sb' style='background:#e8f0fe;color:#1565c0'>Mobile</span>" if is_mobile else ""}</div>
            {"<a class='ad-url' href='"+esc(href)+"' target='_blank'>"+esc(href[:60])+"</a>" if href else ""}
          </div></div>'''

            html += '</div></div>'

        html += '</div></div>'

    # Scripts
    html += '''
<div class="footer">change_tracker v3 | ''' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + '''</div>
</div>
<script>
function toggleCamp(el) { el.classList.toggle('collapsed'); el.nextElementSibling.classList.toggle('hid') }
function toggleGrp(el) { el.nextElementSibling.classList.toggle('open') }

function filterChanges() {
  const t = document.getElementById('chType').value;
  const a = document.getElementById('chAction').value;
  const q = document.getElementById('chSearch').value.toLowerCase();
  document.querySelectorAll('.ch-card').forEach(el => {
    let show = true;
    if (t && el.dataset.type !== t) show = false;
    if (a && el.dataset.action !== a) show = false;
    if (q && !el.textContent.toLowerCase().includes(q)) show = false;
    el.style.display = show ? '' : 'none';
  });
}
function filterState() {
  const q = document.getElementById('stSearch').value.toLowerCase();
  const hideArch = document.getElementById('stHideArch').checked;
  document.querySelectorAll('.grp').forEach(el => {
    let show = true;
    if (hideArch && (el.dataset.status === 'ARCHIVED' || el.dataset.status === 'DRAFT')) show = false;
    if (q && !el.dataset.text.includes(q)) show = false;
    el.style.display = show ? '' : 'none';
  });
}
document.addEventListener('DOMContentLoaded', () => { filterState(); });
</script></body></html>'''
    return html


# ==================== MAIN ====================

def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description="Трекер изменений Яндекс.Директ v3 — BULK + Snapshots")
    p.add_argument("--campaign-ids", help="ID кампаний через запятую (если не указать — ВСЕ)")
    p.add_argument("--days", type=int, default=90, help="Период анализа (дней)")
    p.add_argument("--access-file", help="Защищённый файл доступа Директа")
    p.add_argument("--data-dir", default="./data")
    p.add_argument("--output", help="Путь к HTML")
    p.add_argument("--goal-id", default="", help="Primary goal ID for report metrics")
    p.add_argument("--retention-days", type=int, default=90, help="Срок хранения старых снимков")
    args = p.parse_args()
    access = load_direct_access(args.access_file)
    token, login = access.token, access.client_login
    data_dir = Path(args.data_dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    collection_manifest_path = data_dir / "change-tracker-collection-manifest.json"
    collection_sources = {}
    global GOAL_ID
    if args.goal_id:
        GOAL_ID = args.goal_id

    # 0. Кампании
    if args.campaign_ids:
        cids = [int(x.strip()) for x in args.campaign_ids.split(",")]
    else:
        print("Получаю список ВСЕХ кампаний аккаунта...", flush=True)
        campaign_index = fetch_paginated("campaigns", "get", {
            "SelectionCriteria": {"States": ["ON", "SUSPENDED", "OFF", "ENDED"]},
            "FieldNames": ["Id", "Name"],
        }, "Campaigns", token, login, version="v501", environment=access.environment)
        campaign_index_rows = require_complete(
            campaign_index, "campaign_index", collection_manifest_path, collection_sources
        )
        cids = [c["Id"] for c in campaign_index_rows]
        print(f"Найдено {len(cids)} кампаний", flush=True)
        time.sleep(0.5)

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    report_date = today.isoformat()
    output_path = args.output or os.path.join(args.data_dir, f"changes_report_ALL_{report_date}.html")

    print(f"=== CHANGE TRACKER v3 BULK + SNAPSHOTS ===", flush=True)
    print(f"Кампании: {len(cids)} шт, Период: {args.days} дней\n", flush=True)

    # 1. Changes API — точные ID
    print("1/7 Changes API (checkCampaigns + check)...", flush=True)
    mod_camps, mod_groups, mod_ads, changes_pages = fetch_modified_ids(token, login, cids, args.days, access.environment)
    require_complete(
        completed_result(
            "changes", "ModifiedIds",
            [{"kind": "campaign", "id": value} for value in sorted(mod_camps)]
            + [{"kind": "adgroup", "id": value} for value in sorted(mod_groups)]
            + [{"kind": "ad", "id": value} for value in sorted(mod_ads)],
            pages=changes_pages,
        ),
        "changes",
        collection_manifest_path,
        collection_sources,
    )
    print(f"     Кампаний: {len(mod_camps)}, Групп: {len(mod_groups)}, Объявлений: {len(mod_ads)}", flush=True)
    time.sleep(1)

    # 2. BULK: Кампании
    print("2/7 Кампании (bulk)...", flush=True)
    all_camps = require_complete(fetch_paginated("campaigns", "get", {
        "SelectionCriteria": {"Ids": cids},
        "FieldNames": ["Id", "Name", "Status", "State", "StartDate", "DailyBudget", "NegativeKeywords"],
    }, "Campaigns", token, login, "v501", access.environment), "campaigns", collection_manifest_path, collection_sources)
    camps_by_id = {c["Id"]: c for c in all_camps}
    visible_cids = [cid for cid in cids if cid in camps_by_id]
    print(f"     {len(all_camps)} видимых, {len(cids) - len(all_camps)} невидимых (МК/баннер)", flush=True)
    time.sleep(0.5)

    # 3. BULK: Группы
    print("3/7 Группы (батч по 10)...", flush=True)
    groups_result = fetch_batched("adgroups", "get",
        lambda b: {"SelectionCriteria": {"CampaignIds": b},
                   "FieldNames": ["Id", "Name", "CampaignId", "Status", "RegionIds", "NegativeKeywords"]},
        "AdGroups", visible_cids, 10, token, login, "v501", access.environment) if visible_cids else completed_result("adgroups", "AdGroups", [], 0)
    all_groups = require_complete(groups_result, "adgroups", collection_manifest_path, collection_sources)
    groups_by_camp = {}
    groups_by_id = {}
    for g in all_groups:
        groups_by_camp.setdefault(g["CampaignId"], []).append(g)
        groups_by_id[g["Id"]] = g
    print(f"     {len(all_groups)} групп", flush=True)
    time.sleep(0.5)

    # 4. BULK: Объявления
    print("4/7 Объявления (батч по 10)...", flush=True)
    ads_result = fetch_batched("ads", "get",
        lambda b: {"SelectionCriteria": {"CampaignIds": b},
                   "FieldNames": ["Id", "AdGroupId", "CampaignId", "Status", "State", "Type"],
                   "TextAdFieldNames": ["Title", "Title2", "Text", "Href", "DisplayUrlPath",
                                        "AdImageHash", "SitelinkSetId", "Mobile", "AdExtensions"]},
        "Ads", visible_cids, 10, token, login, "v501", access.environment) if visible_cids else completed_result("ads", "Ads", [], 0)
    all_ads = require_complete(ads_result, "ads", collection_manifest_path, collection_sources)
    ads_by_camp = {}
    for a in all_ads:
        ads_by_camp.setdefault(a["CampaignId"], []).append(a)
    print(f"     {len(all_ads)} объявлений", flush=True)
    time.sleep(0.5)

    # 5. BULK: Ключевые слова
    print("5/7 Ключевые слова (батч по 10)...", flush=True)
    keywords_result = fetch_batched("keywords", "get",
        lambda b: {"SelectionCriteria": {"CampaignIds": b},
                   "FieldNames": ["Id", "Keyword", "AdGroupId", "Status", "State"]},
        "Keywords", visible_cids, 10, token, login, "v5", access.environment) if visible_cids else completed_result("keywords", "Keywords", [], 0)
    all_keywords = require_complete(keywords_result, "keywords", collection_manifest_path, collection_sources)
    gid_to_cid = {g["Id"]: g["CampaignId"] for g in all_groups}
    kws_by_camp = {}
    for k in all_keywords:
        cid_k = gid_to_cid.get(k.get("AdGroupId"))
        if cid_k:
            kws_by_camp.setdefault(cid_k, []).append(k)
    print(f"     {len(all_keywords)} ключевых слов", flush=True)
    time.sleep(0.5)

    # 6. BULK: Изображения
    print("6/7 Изображения (bulk)...", flush=True)
    all_hashes = list(set(
        a.get("TextAd", {}).get("AdImageHash", "") for a in all_ads
        if a.get("TextAd", {}).get("AdImageHash")
    ))
    img_urls = fetch_image_urls(token, login, all_hashes, access.environment) if all_hashes else {}
    require_complete(
        completed_result("adimages", "AdImages", [
            {"hash": value, "url_present": bool(img_urls.get(value))} for value in sorted(all_hashes)
        ], pages=(len(all_hashes) + 49) // 50),
        "adimages",
        collection_manifest_path,
        collection_sources,
    )
    print(f"     {len(all_hashes)} хешей → {len(img_urls)} URL", flush=True)
    time.sleep(0.5)

    # === SNAPSHOT: загрузка предыдущего + сравнение ===
    print("\n=== Snapshot ===", flush=True)
    prev_snap = load_snapshot(args.data_dir)
    cur_snap = build_snapshot(all_camps, all_groups, all_ads, all_keywords)
    snap_date = prev_snap.get("timestamp") if prev_snap else None

    all_changes = []
    if prev_snap:
        print(f"  Предыдущий снимок: {snap_date[:19]}", flush=True)
        # filtered_cids: если запущен с --campaign-ids, передаём set для фильтрации ложных 'deleted'
        filtered_cids = set(cids) if args.campaign_ids else None
        all_changes = compute_all_diffs(cur_snap, prev_snap, mod_camps, mod_groups, mod_ads, camps_by_id, groups_by_id, filtered_cids=filtered_cids)
        print(f"  Найдено изменений: {len(all_changes)}", flush=True)
        n_by_type = {}
        for ch in all_changes:
            n_by_type.setdefault(ch["type"], 0)
            n_by_type[ch["type"]] += 1
        for t, n in sorted(n_by_type.items()):
            print(f"    {t}: {n}", flush=True)
    else:
        print("  Предыдущий снимок не найден — первый запуск", flush=True)

    # Загружаем URL для старых хешей из предыдущего снимка (для диффов изображений)
    if prev_snap and all_changes:
        old_hashes = set()
        for ch in all_changes:
            for d in ch.get("diffs", []):
                if d["field"] == "AdImageHash" and d.get("old") and d["old"] not in img_urls:
                    old_hashes.add(d["old"])
        if old_hashes:
            print(f"  Загрузка {len(old_hashes)} старых изображений...", flush=True)
            old_urls = fetch_image_urls(token, login, list(old_hashes), access.environment)
            img_urls.update(old_urls)
            time.sleep(0.5)

    # Новый снимок сохраняется только после полной выгрузки отчётов ниже.

    # 7. Reports API: статистика до/после снимка
    print("\n7/7 Reports API...", flush=True)
    full_from = (today - datetime.timedelta(days=args.days)).isoformat()
    if snap_date:
        snap_d = snap_date[:10]  # YYYY-MM-DD
        snap_date_obj = datetime.date.fromisoformat(snap_d)
        if snap_date_obj >= yesterday:
            # Снимок от сегодня/вчера — нет "после", один общий период
            label_before = f"Последние {args.days} дн."
            label_after = f"Последние 7 дн."
            before_to = yesterday.isoformat()
            after_from = (today - datetime.timedelta(days=7)).isoformat()
        else:
            label_before = f"до {snap_d}"
            label_after = f"после {snap_d}"
            before_to = snap_d
            after_from = (snap_date_obj + datetime.timedelta(days=1)).isoformat()
    else:
        label_before = f"Последние {args.days} дн."
        label_after = f"Последние 7 дн."
        before_to = yesterday.isoformat()
        after_from = (today - datetime.timedelta(days=7)).isoformat()

    camp_fields = ["CampaignId", "Impressions", "Clicks", "Cost", "Ctr", "AvgCpc",
                    "Conversions", "CostPerConversion", "ConversionRate", "BounceRate"]
    grp_fields = ["CampaignId", "AdGroupId", "Impressions", "Clicks", "Cost", "Ctr",
                   "Conversions", "CostPerConversion"]

    print("     camp before...", flush=True)
    tsv_cb = get_report_bulk("CAMPAIGN_PERFORMANCE_REPORT", camp_fields, full_from, before_to, token, login, data_dir, "bef", environment=access.environment)
    time.sleep(2)
    print("     camp after...", flush=True)
    tsv_ca = get_report_bulk("CAMPAIGN_PERFORMANCE_REPORT", camp_fields, after_from, yesterday.isoformat(), token, login, data_dir, "aft", environment=access.environment)
    time.sleep(2)
    print("     groups...", flush=True)
    tsv_gp = get_report_bulk("ADGROUP_PERFORMANCE_REPORT", grp_fields, full_from, yesterday.isoformat(), token, login, data_dir, "grp", environment=access.environment)
    time.sleep(2)

    # Parse reports
    camp_perf_before = {}
    for r in parse_tsv(tsv_cb):
        cid_s = r.get("CampaignId", "")
        if cid_s and cid_s != "--":
            camp_perf_before[int(cid_s)] = parse_perf_row(r)

    camp_perf_after = {}
    for r in parse_tsv(tsv_ca):
        cid_s = r.get("CampaignId", "")
        if cid_s and cid_s != "--":
            camp_perf_after[int(cid_s)] = parse_perf_row(r)

    grp_perf_all = {}
    for r in parse_tsv(tsv_gp):
        cid_s, gid_s = r.get("CampaignId", ""), r.get("AdGroupId", "")
        if cid_s == "--" or gid_s == "--":
            continue
        try:
            cid_i, gid_i = int(cid_s), int(gid_s)
        except (ValueError, TypeError):
            continue
        def num(k): return float(r.get(k, "0").replace("--", "0"))
        grp_perf_all.setdefault(cid_i, {})[gid_i] = {
            "impressions": int(num("Impressions")), "clicks": int(num("Clicks")),
            "cost": num("Cost"), "ctr": num("Ctr"),
            "conversions": num("Conversions"), "cpa": num("CostPerConversion")}

    require_complete(
        completed_result("reports", "CampaignBeforeRows", parse_tsv(tsv_cb)),
        "report_campaign_before", collection_manifest_path, collection_sources,
    )
    require_complete(
        completed_result("reports", "CampaignAfterRows", parse_tsv(tsv_ca)),
        "report_campaign_after", collection_manifest_path, collection_sources,
    )
    require_complete(
        completed_result("reports", "AdGroupRows", parse_tsv(tsv_gp)),
        "report_adgroups", collection_manifest_path, collection_sources,
    )

    snap_path = save_snapshot(args.data_dir, cur_snap, args.retention_days)
    print(f"  Снимок сохранён: {os.path.basename(snap_path)}", flush=True)

    print(f"     camp_before: {len(camp_perf_before)}, camp_after: {len(camp_perf_after)}, grp: {len(grp_perf_all)}", flush=True)

    # === Сборка campaigns_data ===
    print(f"\n=== Сборка данных ({len(cids)} кампаний) ===", flush=True)
    campaigns_data = []
    for cid in cids:
        camp = camps_by_id.get(cid)
        if not camp:
            continue
        campaigns_data.append({
            "campaign": camp, "groups": groups_by_camp.get(cid, []),
            "ads": ads_by_camp.get(cid, []), "keywords": kws_by_camp.get(cid, []),
            "group_performance": grp_perf_all.get(cid, {}), "login": login,
        })

    # === HTML ===
    print(f"=== Генерация HTML ===", flush=True)
    html = generate_html(all_changes, campaigns_data, report_date, args.days, snap_date, login,
                         camp_perf_before, camp_perf_after, label_before, label_after, img_urls)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        print(html, file=f, flush=True)
    print(f"Отчёт: {output_path}", flush=True)
    print(f"Размер: {len(html) // 1024} KB", flush=True)
    print(f"Изменений: {len(all_changes)}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
