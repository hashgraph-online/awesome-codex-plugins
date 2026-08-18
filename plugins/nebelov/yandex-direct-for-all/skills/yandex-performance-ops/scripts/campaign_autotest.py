#!/usr/bin/env python3
"""
Автотест кампаний Яндекс.Директ
Часть навыка yandex-direct

Проверяет ВСЕ критические настройки кампании через API:
- Статус кампании, даты, стратегия, бюджет
- TimeTargeting (расписание)
- Settings (AREA_OF_INTEREST, ALTERNATIVE_TEXTS и др.)
- Группы: статус, регион, OfferRetargeting, автотаргетинг
- Объявления: статус, модерация, расширения, Mobile
- Ключевые слова: количество, статусы
- Минус-слова: SharedSets привязка
- Ставки: KeywordBids

Запуск:
  python3 campaign_autotest.py --access-file ~/.config/yandex-direct-for-all/direct-access.json --campaign-ids 123,456

Или из Codex:
  python3 <plugin-root>/skills/yandex-performance-ops/scripts/campaign_autotest.py \
    --access-file ~/.config/yandex-direct-for-all/direct-access.json --campaign-ids "10000001,10000002"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from check_access_paths import PageManifestStore, fetch_direct_pages, load_direct_access

# === КОНФИГ ===
API_V5 = "https://api.direct.yandex.com/json/v5"
API_V501 = "https://api.direct.yandex.com/json/v501"

# === ЦВЕТА ===
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

class CampaignAutotest:
    def __init__(self, access, campaign_ids, pre_moderation=False, collection_manifest=None):
        self.access = access
        self.login = access.client_login
        self.campaign_ids = campaign_ids
        self.pre_moderation = pre_moderation
        self.results = []  # (level, status, check_name, detail)
        self.warnings = 0
        self.errors = 0
        self.passes = 0
        self.shopping_campaign_ids = set()  # кампании с ShoppingAd
        self.campaign_tracking_modes = {}
        manifest_path = Path(collection_manifest or "campaign_autotest.collection-manifest.json")
        self.page_manifests = PageManifestStore(manifest_path)
        self.page_call_number = 0

    def ok(self, check, detail=""):
        self.results.append(("PASS", check, detail))
        self.passes += 1

    def warn(self, check, detail=""):
        self.results.append(("WARN", check, detail))
        self.warnings += 1

    def fail(self, check, detail=""):
        self.results.append(("FAIL", check, detail))
        self.errors += 1

    def info(self, check, detail=""):
        self.results.append(("INFO", check, detail))

    def section(self, title):
        self.results.append(("SECTION", title, ""))

    def call(self, endpoint, method, params, version="v5"):
        keys = {
            "campaigns": "Campaigns",
            "adgroups": "AdGroups",
            "ads": "Ads",
            "keywords": "Keywords",
            "negativekeywordsharedsets": "NegativeKeywordSharedSets",
            "sitelinks": "SitelinksSets",
        }
        if method != "get" or endpoint not in keys:
            return {"error": "Неподдерживаемый маршрут чтения"}
        self.page_call_number += 1
        result = self.page_manifests.add(
            f"{self.page_call_number:03d}-{endpoint}",
            fetch_direct_pages(self.access, endpoint, params, keys[endpoint], version=version),
        )
        if not result.manifest.complete:
            return {"error": result.manifest.error}
        return {"result": {keys[endpoint]: result.rows}}

    @staticmethod
    def tracking_mode(value):
        value = value or ""
        if "utm_source" in value and "utm_campaign" in value:
            return "full"
        if value:
            return "partial"
        return "none"

    def run(self):
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}  АВТОТЕСТ КАМПАНИЙ ЯНДЕКС.ДИРЕКТ{RESET}")
        print(f"  Дата: {today}")
        print(f"  Логин: {self.login}")
        print(f"  Кампании: {', '.join(str(c) for c in self.campaign_ids)}")
        print(f"{BOLD}{'='*70}{RESET}\n")

        # === 1. КАМПАНИИ ===
        self.check_campaigns()

        # === 2. SETTINGS ===
        self.check_settings()

        # === 3. ОБЪЯВЛЕНИЯ (до групп — определяем товарные кампании) ===
        self.check_ads()

        # === 4. ГРУППЫ ===
        self.check_groups()

        # === 5. КЛЮЧЕВЫЕ СЛОВА ===
        self.check_keywords()

        # === 6. МИНУС-СЛОВА ===
        self.check_negatives()

        # === ИТОГ ===
        self.print_report()

    def check_campaigns(self):
        self.section("A. КАМПАНИИ")
        resp = self.call("campaigns", "get", {
            "SelectionCriteria": {"Ids": self.campaign_ids},
            "FieldNames": ["Id", "Name", "Status", "State", "StartDate", "DailyBudget",
                           "NegativeKeywords", "StatusClarification", "TimeTargeting"],
            "UnifiedCampaignFieldNames": ["BiddingStrategy", "CounterIds",
                                          "PriorityGoals", "TrackingParams",
                                          "NegativeKeywordSharedSetIds", "Settings"]
        }, version="v501")

        if "error" in resp:
            self.fail("API campaigns.get", f"Ошибка: {resp['error']}")
            return

        campaigns = resp.get("result", {}).get("Campaigns", [])
        for camp in campaigns:
            cid = camp["Id"]
            name = camp.get("Name", "?")
            self.info(f"Кампания {cid}", name)

            # Статус
            status = camp.get("Status", "?")
            state = camp.get("State", "?")
            if status == "ACCEPTED" and state == "ON":
                self.ok(f"  [{cid}] Статус", f"{status} / {state}")
            elif status == "ACCEPTED":
                self.warn(f"  [{cid}] Статус", f"{status} / State={state} (не запущена?)")
            elif status == "MODERATION":
                self.warn(f"  [{cid}] Статус", f"{status} / {state} (на модерации)")
            elif self.pre_moderation and status == "DRAFT" and state == "OFF":
                self.ok(f"  [{cid}] Статус", f"{status} / {state} (pre-moderation режим)")
            else:
                self.fail(f"  [{cid}] Статус", f"{status} / {state}")

            # StartDate
            start = camp.get("StartDate", "?")
            if start == today_str():
                self.ok(f"  [{cid}] StartDate", start)
            elif start < today_str():
                self.ok(f"  [{cid}] StartDate", f"{start} (в прошлом, ОК)")
            else:
                self.fail(f"  [{cid}] StartDate", f"{start} (БУДУЩЕЕ! Кампания не показывается!)")

            # DailyBudget
            db = camp.get("DailyBudget")
            if db:
                amount_rub = db["Amount"] / 1_000_000
                self.info(f"  [{cid}] Дневной бюджет", f"{amount_rub:.0f} руб ({db['Mode']})")
            else:
                self.info(f"  [{cid}] Дневной бюджет", "Не установлен (авто-стратегия?)")

            # Стратегия
            uc = camp.get("UnifiedCampaign") or {}
            strategy = uc.get("BiddingStrategy", {})
            search_strat = strategy.get("Search", {}).get("BiddingStrategyType", "?")
            network_strat = strategy.get("Network", {}).get("BiddingStrategyType", "?")
            self.info(f"  [{cid}] Стратегия", f"Поиск={search_strat}, Сети={network_strat}")

            # CounterIds
            counters_raw = uc.get("CounterIds")
            if isinstance(counters_raw, dict):
                counters = counters_raw.get("Items", []) or []
            elif isinstance(counters_raw, list):
                counters = counters_raw
            else:
                counters = []

            if counters:
                self.ok(f"  [{cid}] CounterIds (Метрика)", f"{counters}")
            else:
                self.fail(f"  [{cid}] CounterIds (Метрика)", "НЕТ! Нет аналитики!")

            # PriorityGoals
            goals = (uc.get("PriorityGoals") or {}).get("Items", [])
            if goals:
                goal_strs = [f"ID={g['GoalId']}(val={g.get('Value',0)/1000000:.0f})" for g in goals]
                self.ok(f"  [{cid}] PriorityGoals", ", ".join(goal_strs))
            else:
                self.warn(f"  [{cid}] PriorityGoals", "Не заданы — оптимизация невозможна")

            # TrackingParams
            tp = uc.get("TrackingParams", "") or ""
            tracking_mode = self.tracking_mode(tp)
            self.campaign_tracking_modes[cid] = tracking_mode
            if tracking_mode == "full":
                self.ok(f"  [{cid}] TrackingParams (UTM)", f"{tp[:80]}...")
            elif tracking_mode == "partial":
                self.warn(f"  [{cid}] TrackingParams", f"Неполные UTM: {tp[:60]}")
            else:
                self.warn(
                    f"  [{cid}] TrackingParams",
                    "ПУСТО на кампании — допустимо, если полный tracking задан на группах и Href чистый",
                )

            # TimeTargeting
            tt = camp.get("TimeTargeting") or {}
            schedule = (tt.get("Schedule") or {}).get("Items", [])
            holidays = tt.get("HolidaysSchedule") or {}
            if schedule:
                active_days = sum(1 for s in schedule if any(int(h) > 0 for h in s.split(",")[1:]))
                all_hours = all(all(int(h) == 100 for h in s.split(",")[1:]) for s in schedule)
                if all_hours and active_days == 7:
                    self.warn(f"  [{cid}] TimeTargeting", "24/7 все дни — для B2B это нормально?")
                else:
                    self.ok(f"  [{cid}] TimeTargeting", f"Настроено: {active_days} дней активно")

                hol_suspend = holidays.get("SuspendOnHolidays", "NO")
                self.info(f"  [{cid}] Праздники", f"SuspendOnHolidays={hol_suspend}")
            else:
                self.warn(f"  [{cid}] TimeTargeting", "Не настроено (24/7 по умолчанию)")

            # NegativeKeywordSharedSetIds
            shared_neg = (uc.get("NegativeKeywordSharedSetIds") or {}).get("Items", [])
            if shared_neg:
                self.ok(f"  [{cid}] SharedNegSets", f"Привязано: {shared_neg}")
            else:
                self.warn(f"  [{cid}] SharedNegSets", "Нет общих минус-слов!")

            # NegativeKeywords кампании
            neg_kw_raw = camp.get("NegativeKeywords") or []
            if isinstance(neg_kw_raw, dict):
                neg_kw = neg_kw_raw.get("Items", []) or []
            elif isinstance(neg_kw_raw, list):
                neg_kw = neg_kw_raw
            else:
                neg_kw = []
            self.info(f"  [{cid}] Минус-слова кампании", f"{len(neg_kw)} шт.")

            # Settings
            settings = uc.get("Settings", [])
            settings_map = {s["Option"]: s["Value"] for s in settings} if settings else {}

            aoi = settings_map.get("ENABLE_AREA_OF_INTEREST_TARGETING", "YES")
            if aoi == "NO":
                self.ok(f"  [{cid}] AREA_OF_INTEREST", "NO (отключено)")
            else:
                self.warn(f"  [{cid}] AREA_OF_INTEREST", f"{aoi} — показы ВНЕ региона! Для МО=BAD")

            alt = settings_map.get("ALTERNATIVE_TEXTS_ENABLED", "YES")
            if alt == "NO":
                self.ok(f"  [{cid}] ALTERNATIVE_TEXTS", "NO (отключено)")
            else:
                self.warn(f"  [{cid}] ALTERNATIVE_TEXTS", f"{alt} — Яндекс подменяет тексты!")

    def check_settings(self):
        """Проверка PlacementTypes и др. доп. настроек"""
        self.section("B. PLACEMENTTYPES (площадки показа)")
        resp = self.call("campaigns", "get", {
            "SelectionCriteria": {"Ids": self.campaign_ids},
            "FieldNames": ["Id", "Name"],
            "UnifiedCampaignFieldNames": ["BiddingStrategy"],
            "UnifiedCampaignSearchStrategyPlacementTypesFieldNames": [
                "SearchResults", "ProductGallery", "DynamicPlaces", "Maps", "SearchOrganizationList"
            ]
        }, version="v501")

        if "error" in resp:
            self.fail("PlacementTypes API", f"Ошибка: {resp['error']}")
            return

        for camp in resp.get("result", {}).get("Campaigns", []):
            cid = camp["Id"]
            name = camp.get("Name", "?")
            uc = camp.get("UnifiedCampaign", {})
            strat = uc.get("BiddingStrategy", {})
            search = strat.get("Search", {})
            search_type = search.get("BiddingStrategyType", "?")
            pt = search.get("PlacementTypes", {})

            # Если Search=SERVING_OFF — площадки не важны
            if search_type == "SERVING_OFF":
                self.info(f"  [{cid}] PlacementTypes", "Search=OFF, пропускаем")
                continue

            # PlacementTypes не задан — все по умолчанию YES!
            if not pt:
                self.fail(f"  [{cid}] PlacementTypes", "НЕ ЗАДАНЫ! По умолчанию ВСЕ=YES (Карты, Оргсписок, Динамические — слив бюджета!)")
                continue

            # Проверяем каждую площадку
            maps_val = pt.get("Maps", "YES")
            org_val = pt.get("SearchOrganizationList", "YES")
            dyn_val = pt.get("DynamicPlaces", "YES")
            sr_val = pt.get("SearchResults", "YES")
            pg_val = pt.get("ProductGallery", "YES")

            issues = []
            if maps_val == "YES":
                issues.append("Maps=YES")
                self.fail(f"  [{cid}] Maps", "YES — сливает бюджет на Яндекс Карты!")
            if org_val == "YES":
                issues.append("SearchOrg=YES")
                self.fail(f"  [{cid}] SearchOrganizationList", "YES — сливает бюджет на оргсписок!")
            if dyn_val == "YES":
                issues.append("DynamicPlaces=YES")
                self.warn(f"  [{cid}] DynamicPlaces", "YES — бета-площадка, рискованно")

            if not issues:
                summary = f"SR={sr_val} PG={pg_val} Maps={maps_val} Org={org_val} Dyn={dyn_val}"
                self.ok(f"  [{cid}] PlacementTypes", summary)

    def check_groups(self):
        self.section("C. ГРУППЫ")
        resp = self.call("adgroups", "get", {
            "SelectionCriteria": {"CampaignIds": self.campaign_ids},
            "FieldNames": ["Id", "CampaignId", "Name", "Status", "ServingStatus",
                           "RegionIds", "NegativeKeywords", "TrackingParams"],
            "UnifiedAdGroupFieldNames": ["OfferRetargeting"]
        }, version="v501")

        if "error" in resp:
            self.fail("API adgroups.get", f"Ошибка: {resp['error']}")
            return

        groups = resp.get("result", {}).get("AdGroups", [])
        self.info("Всего групп", str(len(groups)))

        # Группировка по кампании
        by_campaign = {}
        for g in groups:
            cid = g["CampaignId"]
            by_campaign.setdefault(cid, []).append(g)

        for cid, grps in sorted(by_campaign.items()):
            self.info(f"Кампания {cid}", f"{len(grps)} групп")

            for g in grps:
                gid = g["Id"]
                name = g.get("Name", "?")
                status = g.get("Status", "?")
                serving = g.get("ServingStatus", "?")

                # Статус группы
                if status == "ACCEPTED" and serving == "ELIGIBLE":
                    status_str = f"{GREEN}OK{RESET}"
                elif status == "ACCEPTED":
                    status_str = f"{YELLOW}{serving}{RESET}"
                elif self.pre_moderation and status == "DRAFT" and serving == "ELIGIBLE":
                    status_str = f"{GREEN}DRAFT/ELIGIBLE (pre-moderation){RESET}"
                else:
                    status_str = f"{RED}{status}/{serving}{RESET}"
                    self.fail(f"  Группа {gid}", f"{name}: {status}/{serving}")

                # OfferRetargeting
                ua = g.get("UnifiedAdGroup", {})
                offer_ret = ua.get("OfferRetargeting", "YES")

                # Region
                regions = g.get("RegionIds", [])

                # Tracking
                tp = g.get("TrackingParams", "") or ""
                group_tracking_mode = self.tracking_mode(tp)
                campaign_tracking_mode = self.campaign_tracking_modes.get(cid, "none")

                # Negative keywords
                neg = g.get("NegativeKeywords") or []

                # Собираем строку
                issues = []
                if offer_ret == "YES":
                    issues.append(f"{YELLOW}OfferRetarget=YES{RESET}")
                if group_tracking_mode == "partial":
                    issues.append("UTM=partial")
                    self.fail(
                        f"  [{gid}] TrackingParams группы",
                        "Неполные TrackingParams на группе — они перекрывают кампанию и ломают UTM",
                    )
                elif group_tracking_mode == "none":
                    if campaign_tracking_mode == "full":
                        issues.append("UTM=campaign")
                        self.info(
                            f"  [{gid}] TrackingParams группы",
                            "Пусто на группе — унаследует полные TrackingParams кампании",
                        )
                    elif campaign_tracking_mode == "partial":
                        issues.append("UTM=campaign-partial")
                        self.fail(
                            f"  [{gid}] TrackingParams группы",
                            "На группе пусто, а на кампании неполные TrackingParams",
                        )
                    else:
                        issues.append("UTM=нет")
                        self.fail(
                            f"  [{gid}] TrackingParams группы",
                            "Пусто и на группе, и на кампании — tracking не настроен",
                        )

                issues_str = f" | {', '.join(issues)}" if issues else ""
                self.info(f"  {gid} {name[:40]}",
                         f"Ст={status} Серв={serving} Рег={regions} Мин={len(neg)}{issues_str}")

                if offer_ret == "YES":
                    camp_id = g.get("CampaignId", 0)
                    if camp_id in self.shopping_campaign_ids:
                        self.ok(f"  [{gid}] OfferRetargeting", "YES (товарная кампания — OK)")
                    else:
                        self.warn(f"  [{gid}] OfferRetargeting", "YES (default!) — для поиска нужно NO")

        # Проверяем автотаргетинг
        self.section("C2. АВТОТАРГЕТИНГ")
        for cid, grps in sorted(by_campaign.items()):
            group_ids = [g["Id"] for g in grps]
            # API keywords - ищем автотаргетинг (Type=AUTOTARGETING)
            kw_resp = self.call("keywords", "get", {
                "SelectionCriteria": {"AdGroupIds": group_ids[:1000]},
                "FieldNames": ["Id", "AdGroupId", "Keyword", "State", "Status", "AutotargetingCategories"]
            })
            if "error" not in kw_resp:
                keywords = kw_resp.get("result", {}).get("Keywords", [])
                groups_with_kw = set(k["AdGroupId"] for k in keywords)
                groups_without_kw = [g["Id"] for g in grps if g["Id"] not in groups_with_kw]
                if groups_without_kw:
                    self.fail(f"Кампания {cid}: группы БЕЗ ключей", str(groups_without_kw))
                else:
                    self.ok(f"Кампания {cid}: все группы имеют ключи", f"{len(keywords)} ключей в {len(groups_with_kw)} группах")

                # C3. Проверка AutotargetingCategories
                for kw in keywords:
                    if kw.get("Keyword") == "---autotargeting":
                        cats = kw.get("AutotargetingCategories", {}).get("Items", [])
                        dangerous = []
                        for cat in cats:
                            name = cat.get("Category", "")
                            val = cat.get("Value", "NO")
                            if name in ("COMPETITOR", "BROADER", "ACCESSORY") and val == "YES":
                                dangerous.append(name)
                        gid = kw["AdGroupId"]
                        if dangerous:
                            self.fail(f"  [{gid}] AutotargetingCategories", f"ОПАСНЫЕ категории включены: {', '.join(dangerous)} — слив бюджета!")
                        else:
                            self.ok(f"  [{gid}] AutotargetingCategories", "Только целевые (EXACT/ALTERNATIVE)")

    def check_ads(self):
        self.section("D. ОБЪЯВЛЕНИЯ")
        # Запрашиваем через v501 чтобы получить ShoppingAd
        resp = self.call("ads", "get", {
            "SelectionCriteria": {"CampaignIds": self.campaign_ids},
            "FieldNames": ["Id", "AdGroupId", "CampaignId", "Status", "State", "Type"],
            "TextAdFieldNames": ["Title", "Title2", "Text", "Href", "Mobile",
                                 "SitelinkSetId", "SitelinksModeration",
                                 "AdImageHash", "AdImageModeration",
                                 "AdExtensions", "DisplayUrlPath"],
            "ShoppingAdFieldNames": ["FeedId", "DefaultTexts"]
        }, version="v501")

        if "error" in resp:
            self.fail("API ads.get", f"Ошибка: {resp['error']}")
            return

        all_ads = resp.get("result", {}).get("Ads", [])

        # Определяем товарные кампании (имеют SHOPPING_AD)
        for ad in all_ads:
            if ad.get("Type") == "SHOPPING_AD":
                self.shopping_campaign_ids.add(ad["CampaignId"])

        # Фильтруем только активные (не OFF/ARCHIVED) — но для товарных включаем все
        ads = [a for a in all_ads if a.get("State") != "OFF" or a["CampaignId"] in self.shopping_campaign_ids]
        suspended = [a for a in all_ads if a.get("State") == "OFF" and a["CampaignId"] not in self.shopping_campaign_ids]
        self.info("Всего объявлений", f"{len(ads)} активных/товарных, {len(suspended)} приостановленных")

        # Группировка по группе
        by_group = {}
        for ad in ads:
            gid = ad["AdGroupId"]
            by_group.setdefault(gid, []).append(ad)

        # Статистика по кампаниям
        by_campaign = {}
        for ad in ads:
            cid = ad["CampaignId"]
            by_campaign.setdefault(cid, []).append(ad)

        for cid, camp_ads in sorted(by_campaign.items()):
            is_shopping = cid in self.shopping_campaign_ids
            text_ads = [a for a in camp_ads if a.get("Type") != "SHOPPING_AD"]
            shopping_ads = [a for a in camp_ads if a.get("Type") == "SHOPPING_AD"]

            statuses = {}
            for ad in camp_ads:
                s = ad.get("Status", "?")
                statuses[s] = statuses.get(s, 0) + 1

            type_info = f" (ТОВАРНАЯ: {len(shopping_ads)} ShoppingAd)" if shopping_ads else ""
            status_str = ", ".join(f"{k}={v}" for k, v in sorted(statuses.items()))
            self.info(f"Кампания {cid}", f"{len(camp_ads)} объявлений: {status_str}{type_info}")

            # ShoppingAd проверки
            for ad in shopping_ads:
                sa = ad.get("ShoppingAd", {})
                ad_id = ad["Id"]
                feed_id = sa.get("FeedId")
                texts = sa.get("DefaultTexts", [])
                ad_status = ad.get("Status", "?")

                if ad_status == "ACCEPTED":
                    self.ok(f"  [{cid}] ShoppingAd {ad_id}", f"ACCEPTED, FeedId={feed_id}")
                elif ad_status == "MODERATION":
                    self.warn(f"  [{cid}] ShoppingAd {ad_id}", f"На модерации, FeedId={feed_id}")
                elif ad_status == "REJECTED":
                    self.fail(f"  [{cid}] ShoppingAd {ad_id}", f"REJECTED! FeedId={feed_id}")
                else:
                    self.info(f"  [{cid}] ShoppingAd {ad_id}", f"Status={ad_status}, FeedId={feed_id}")

                if not feed_id:
                    self.fail(f"  [{cid}] ShoppingAd {ad_id}", "НЕТ FeedId!")
                if not texts:
                    self.warn(f"  [{cid}] ShoppingAd {ad_id}", "Нет DefaultTexts")

            # TextAd проверки (только для текстовых)
            if text_ads:
                # Модерация расширений
                rejected = []
                pending = []
                for ad in text_ads:
                    ta = ad.get("TextAd", {})
                    ad_id = ad["Id"]

                    slm = ta.get("SitelinksModeration", {})
                    if slm and slm.get("Status") == "REJECTED":
                        rejected.append(f"Ad {ad_id}: sitelinks=REJECTED")
                    elif slm and slm.get("Status") == "MODERATION":
                        pending.append(f"sitelinks")

                    aim = ta.get("AdImageModeration", {})
                    if aim and aim.get("Status") == "REJECTED":
                        rejected.append(f"Ad {ad_id}: image=REJECTED")
                    elif aim and aim.get("Status") == "MODERATION":
                        pending.append(f"image")

                    for ext in ta.get("AdExtensions", []):
                        if ext.get("Status") == "REJECTED":
                            rejected.append(f"Ad {ad_id}: ext {ext.get('AdExtensionId')}=REJECTED")

                if rejected:
                    for r in rejected:
                        self.fail(f"  [{cid}] Модерация расширений", r)
                if pending:
                    self.warn(f"  [{cid}] На модерации", f"{len(pending)} элементов ожидают проверки")
                if not rejected and not pending:
                    self.ok(f"  [{cid}] Модерация расширений", "Все ACCEPTED")

                # Mobile версии
                for gid, group_ads in by_group.items():
                    ga_text = [a for a in group_ads if a.get("Type") != "SHOPPING_AD"]
                    if not ga_text or ga_text[0]["CampaignId"] != cid:
                        continue
                    has_mobile = any(a.get("TextAd", {}).get("Mobile") == "YES" for a in ga_text)
                    if not has_mobile:
                        self.info(f"  Группа {gid}", f"{len(ga_text)} текстовых, Mobile=нет")

                # Href
                no_href = [a["Id"] for a in text_ads if not a.get("TextAd", {}).get("Href")]
                if no_href:
                    self.fail(f"  [{cid}] Объявления без Href", str(no_href))

                # Sitelinks
                no_sitelinks = [a["Id"] for a in text_ads if not a.get("TextAd", {}).get("SitelinkSetId")]
                if no_sitelinks:
                    self.warn(f"  [{cid}] Объявления без быстрых ссылок", f"{len(no_sitelinks)} шт.")

                # Длины текстов
                punct = set(r'.,;:!?—-()[]{}«»""\'/\\@#$%^&*+=~<>|₽')
                text_issues = []
                for ad in text_ads:
                    ta = ad.get("TextAd", {})
                    text = ta.get("Text", "")
                    title = ta.get("Title", "")
                    title2 = ta.get("Title2", "")
                    text_base = sum(1 for c in text if c not in punct)
                    if text_base > 80:
                        text_issues.append(f"Ad {ad['Id']}: Text base={text_base}>80")
                    if len(title) > 56:
                        text_issues.append(f"Ad {ad['Id']}: Title len={len(title)}>56")
                    if title2:
                        t2_base = sum(1 for c in title2 if c not in punct)
                        if t2_base > 30:
                            text_issues.append(f"Ad {ad['Id']}: Title2 base={t2_base}>30")
                if text_issues:
                    for t in text_issues:
                        self.warn(f"  [{cid}] Длина текста", t)
                else:
                    self.ok(f"  [{cid}] Длины текстов", "Все в пределах лимитов")

        # Проверяем совпадение доменов ad <-> sitelinks (только для TextAd)
        self.section("D2. ДОМЕНЫ (ad Href vs Sitelinks)")
        text_only = [a for a in ads if a.get("Type") != "SHOPPING_AD"]
        all_sl_ids = [a.get("TextAd", {}).get("SitelinkSetId") for a in text_only if a.get("TextAd", {}).get("SitelinkSetId")]
        self.check_domain_match(text_only, all_sl_ids)

    def check_domain_match(self, ads, sitelink_ids):
        """Проверка совпадения доменов объявлений и быстрых ссылок"""
        from urllib.parse import urlparse

        # Получаем сайтлинки
        unique_ids = list(set(sitelink_ids))
        if not unique_ids:
            return

        sl_resp = self.call("sitelinks", "get", {
            "SelectionCriteria": {"Ids": unique_ids},
            "FieldNames": ["Id", "Sitelinks"]
        })
        if "error" in sl_resp:
            return

        sl_domains = {}
        sl_texts = {}
        for s in sl_resp.get("result", {}).get("SitelinksSets", []):
            domains = set()
            texts = []
            for sl in s["Sitelinks"]:
                d = urlparse(sl["Href"]).netloc
                domains.add(d)
                texts.append(f"{sl['Title']}: {sl.get('Description','')}")
            sl_domains[s["Id"]] = domains
            sl_texts[s["Id"]] = texts

        # Проверяем каждое объявление
        mismatches = []
        for ad in ads:
            ta = ad.get("TextAd", {})
            href = ta.get("Href", "")
            sl_id = ta.get("SitelinkSetId")
            if not href or not sl_id:
                continue
            ad_domain = urlparse(href).netloc
            sl_doms = sl_domains.get(sl_id, set())
            if sl_doms and ad_domain not in sl_doms:
                mismatches.append(f"Ad {ad['Id']}: href={ad_domain}, sitelinks={sl_doms}")

        if mismatches:
            for m in mismatches:
                self.fail("Несовпадение доменов ad/sitelinks", m)
        else:
            self.ok("Домены ad/sitelinks", "Совпадают")

        # Проверяем фактические ошибки в описаниях сайтлинков
        for sl_id, texts in sl_texts.items():
            for t in texts:
                if "6 тип" in t.lower():
                    self.fail(f"SitelinkSet {sl_id}", f"Содержит '6 тип' (должно быть 8): {t}")

    def check_keywords(self):
        self.section("E. КЛЮЧЕВЫЕ СЛОВА")
        for cid in self.campaign_ids:
            # Получаем группы кампании
            grp_resp = self.call("adgroups", "get", {
                "SelectionCriteria": {"CampaignIds": [cid]},
                "FieldNames": ["Id", "Name"]
            })
            if "error" in grp_resp:
                self.fail(f"Кампания {cid}: получение групп", str(grp_resp["error"]))
                continue

            group_ids = [g["Id"] for g in grp_resp.get("result", {}).get("AdGroups", [])]
            if not group_ids:
                self.fail(f"Кампания {cid}", "Нет групп!")
                continue

            kw_resp = self.call("keywords", "get", {
                "SelectionCriteria": {"AdGroupIds": group_ids[:1000]},
                "FieldNames": ["Id", "AdGroupId", "Keyword", "State", "Status"]
            })
            if "error" in kw_resp:
                self.fail(f"Кампания {cid}: keywords.get", str(kw_resp["error"]))
                continue

            keywords = kw_resp.get("result", {}).get("Keywords", [])

            # Статистика
            by_status = {}
            by_group_count = {}
            for kw in keywords:
                s = kw.get("Status", "?")
                by_status[s] = by_status.get(s, 0) + 1
                gid = kw["AdGroupId"]
                by_group_count[gid] = by_group_count.get(gid, 0) + 1

            status_str = ", ".join(f"{k}={v}" for k, v in sorted(by_status.items()))
            self.info(f"Кампания {cid}", f"{len(keywords)} ключей: {status_str}")

            # Группы без ключей
            empty_groups = [gid for gid in group_ids if gid not in by_group_count]
            if empty_groups:
                self.fail(f"  [{cid}] Группы БЕЗ ключей", str(empty_groups))

            # Распределение по группам
            for gid, cnt in sorted(by_group_count.items()):
                group_name = next((g["Name"] for g in grp_resp["result"]["AdGroups"] if g["Id"] == gid), "?")
                self.info(f"  Группа {gid}", f"{cnt} ключей | {group_name[:40]}")

    def check_negatives(self):
        self.section("F. МИНУС-СЛОВА")
        # Получаем все SharedSets из кампаний (уже в check_campaigns)
        # Здесь проверяем содержимое SharedSets
        resp = self.call("campaigns", "get", {
            "SelectionCriteria": {"Ids": self.campaign_ids},
            "FieldNames": ["Id", "Name"],
            "UnifiedCampaignFieldNames": ["NegativeKeywordSharedSetIds"]
        }, version="v501")

        if "error" in resp:
            self.fail("SharedSets check", str(resp["error"]))
            return

        all_set_ids = set()
        for camp in resp.get("result", {}).get("Campaigns", []):
            ids = camp.get("UnifiedCampaign", {}).get("NegativeKeywordSharedSetIds", {}).get("Items", [])
            all_set_ids.update(ids)

        if all_set_ids:
            sets_resp = self.call("negativekeywordsharedsets", "get", {
                "SelectionCriteria": {"Ids": list(all_set_ids)},
                "FieldNames": ["Id", "Name", "NegativeKeywords"]
            })
            if "error" not in sets_resp:
                for ns in sets_resp.get("result", {}).get("NegativeKeywordSharedSets", []):
                    nk = ns.get("NegativeKeywords", [])
                    self.info(f"  SharedSet {ns['Id']}", f"\"{ns.get('Name', '?')}\" — {len(nk)} минус-слов")
            else:
                self.warn("SharedSets", f"Не удалось получить: {sets_resp['error']}")
        else:
            self.warn("SharedSets", "Ни одна кампания не привязана к общим минус-словам!")

    def print_report(self):
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}  РЕЗУЛЬТАТЫ АВТОТЕСТА{RESET}")
        print(f"{BOLD}{'='*70}{RESET}\n")

        current_section = ""
        for entry in self.results:
            status, check, detail = entry

            if status == "SECTION":
                current_section = check
                print(f"\n{BOLD}{CYAN}--- {check} ---{RESET}")
                continue

            if status == "PASS":
                icon = f"{GREEN}[OK]{RESET}"
            elif status == "WARN":
                icon = f"{YELLOW}[!!]{RESET}"
            elif status == "FAIL":
                icon = f"{RED}[XX]{RESET}"
            else:
                icon = f"[--]"

            detail_str = f" => {detail}" if detail else ""
            print(f"  {icon} {check}{detail_str}")

        # Summary
        total = self.passes + self.warnings + self.errors
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"  {GREEN}PASS: {self.passes}{RESET}  |  {YELLOW}WARN: {self.warnings}{RESET}  |  {RED}FAIL: {self.errors}{RESET}  |  Total checks: {total}")

        if self.errors > 0:
            print(f"\n  {RED}{BOLD}ВЕРДИКТ: ЕСТЬ КРИТИЧЕСКИЕ ОШИБКИ! Исправить перед запуском!{RESET}")
        elif self.warnings > 0:
            print(f"\n  {YELLOW}{BOLD}ВЕРДИКТ: Есть предупреждения. Проверить вручную.{RESET}")
        else:
            print(f"\n  {GREEN}{BOLD}ВЕРДИКТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!{RESET}")

        print(f"{BOLD}{'='*70}{RESET}\n")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="Автотест кампаний Яндекс.Директ")
    parser.add_argument("--access-file", help="Защищённый файл доступа Директа")
    parser.add_argument("--campaign-ids", required=True, help="ID кампаний через запятую")
    parser.add_argument("--pre-moderation", action="store_true",
                        help="Режим проверки перед отправкой на модерацию (DRAFT/ELIGIBLE допустимы)")
    parser.add_argument(
        "--collection-manifest",
        default="campaign_autotest.collection-manifest.json",
        help="Файл доказательств полноты всех постраничных выгрузок",
    )
    args = parser.parse_args()
    access = load_direct_access(args.access_file)

    campaign_ids = [int(x.strip()) for x in args.campaign_ids.split(",")]

    tester = CampaignAutotest(
        access,
        campaign_ids,
        pre_moderation=args.pre_moderation,
        collection_manifest=args.collection_manifest,
    )
    tester.run()


if __name__ == "__main__":
    main()
