import type { GoalProgressMessages } from "../locale.js";
import { amMessages } from "./am.js";
import { arMessages } from "./ar.js";
import { bgMessages } from "./bg.js";
import { bnMessages } from "./bn.js";
import { bsMessages } from "./bs.js";
import { caMessages } from "./ca.js";
import { csMessages } from "./cs.js";
import { daMessages } from "./da.js";
import { deMessages } from "./de.js";
import { elMessages } from "./el.js";
import { enMessages } from "./en.js";
import { es419Messages } from "./es-419.js";
import { esESMessages } from "./es-es.js";
import { etMessages } from "./et.js";
import { faMessages } from "./fa.js";
import { fiMessages } from "./fi.js";
import { frCAMessages } from "./fr-ca.js";
import { frFRMessages } from "./fr-fr.js";
import { guMessages } from "./gu.js";
import { hiMessages } from "./hi.js";
import { hrMessages } from "./hr.js";
import { huMessages } from "./hu.js";
import { hyMessages } from "./hy.js";
import { idMessages } from "./id.js";
import { isISMessages } from "./is.js";
import { itMessages } from "./it.js";
import { jaMessages } from "./ja.js";
import { kaMessages } from "./ka.js";
import { kkMessages } from "./kk.js";
import { knMessages } from "./kn.js";
import { koMessages } from "./ko.js";
import { ltMessages } from "./lt.js";
import { lvMessages } from "./lv.js";
import { mkMessages } from "./mk.js";
import { mlMessages } from "./ml.js";
import { mnMessages } from "./mn.js";
import { mrMessages } from "./mr.js";
import { msMessages } from "./ms.js";
import { myMessages } from "./my.js";
import { nbMessages } from "./nb.js";
import { nlMessages } from "./nl.js";
import { paMessages } from "./pa.js";
import { plMessages } from "./pl.js";
import { ptBRMessages } from "./pt-br.js";
import { ptPTMessages } from "./pt-pt.js";
import { roMessages } from "./ro.js";
import { ruMessages } from "./ru.js";
import { skMessages } from "./sk.js";
import { slMessages } from "./sl.js";
import { soMessages } from "./so.js";
import { sqMessages } from "./sq.js";
import { srMessages } from "./sr.js";
import { svMessages } from "./sv.js";
import { swMessages } from "./sw.js";
import { taMessages } from "./ta.js";
import { teMessages } from "./te.js";
import { thMessages } from "./th.js";
import { tlMessages } from "./tl.js";
import { trMessages } from "./tr.js";
import { ukMessages } from "./uk.js";
import { urMessages } from "./ur.js";
import { viMessages } from "./vi.js";
import { zhCNMessages } from "./zh-cn.js";
import { zhHKMessages } from "./zh-hk.js";
import { zhTWMessages } from "./zh-tw.js";

export const GOAL_PROGRESS_SUPPORTED_LOCALES = Object.freeze([
  "en-US",
  "am",
  "ar",
  "bg-BG",
  "bn-BD",
  "bs-BA",
  "ca-ES",
  "cs-CZ",
  "da-DK",
  "de-DE",
  "el-GR",
  "es-419",
  "es-ES",
  "et-EE",
  "fa",
  "fi-FI",
  "fr-CA",
  "fr-FR",
  "gu-IN",
  "hi-IN",
  "hr-HR",
  "hu-HU",
  "hy-AM",
  "id-ID",
  "is-IS",
  "it-IT",
  "ja-JP",
  "ka-GE",
  "kk",
  "kn-IN",
  "ko-KR",
  "lt",
  "lv-LV",
  "mk-MK",
  "ml",
  "mn",
  "mr-IN",
  "ms-MY",
  "my-MM",
  "nb-NO",
  "nl-NL",
  "pa",
  "pl-PL",
  "pt-BR",
  "pt-PT",
  "ro-RO",
  "ru-RU",
  "sk-SK",
  "sl-SI",
  "so-SO",
  "sq-AL",
  "sr-RS",
  "sv-SE",
  "sw-TZ",
  "ta-IN",
  "te-IN",
  "th-TH",
  "tl",
  "tr-TR",
  "uk-UA",
  "ur",
  "vi-VN",
  "zh-CN",
  "zh-HK",
  "zh-TW",
] as const);

export const goalProgressCatalogs: ReadonlyMap<string, GoalProgressMessages> = new Map([
  ["en-US", enMessages],
  ["am", amMessages],
  ["ar", arMessages],
  ["bg-BG", bgMessages],
  ["bn-BD", bnMessages],
  ["bs-BA", bsMessages],
  ["ca-ES", caMessages],
  ["cs-CZ", csMessages],
  ["da-DK", daMessages],
  ["de-DE", deMessages],
  ["el-GR", elMessages],
  ["es-419", es419Messages],
  ["es-ES", esESMessages],
  ["et-EE", etMessages],
  ["fa", faMessages],
  ["fi-FI", fiMessages],
  ["fr-CA", frCAMessages],
  ["fr-FR", frFRMessages],
  ["gu-IN", guMessages],
  ["hi-IN", hiMessages],
  ["hr-HR", hrMessages],
  ["hu-HU", huMessages],
  ["hy-AM", hyMessages],
  ["id-ID", idMessages],
  ["is-IS", isISMessages],
  ["it-IT", itMessages],
  ["ja-JP", jaMessages],
  ["ka-GE", kaMessages],
  ["kk", kkMessages],
  ["kn-IN", knMessages],
  ["ko-KR", koMessages],
  ["lt", ltMessages],
  ["lv-LV", lvMessages],
  ["mk-MK", mkMessages],
  ["ml", mlMessages],
  ["mn", mnMessages],
  ["mr-IN", mrMessages],
  ["ms-MY", msMessages],
  ["my-MM", myMessages],
  ["nb-NO", nbMessages],
  ["nl-NL", nlMessages],
  ["pa", paMessages],
  ["pl-PL", plMessages],
  ["pt-BR", ptBRMessages],
  ["pt-PT", ptPTMessages],
  ["ro-RO", roMessages],
  ["ru-RU", ruMessages],
  ["sk-SK", skMessages],
  ["sl-SI", slMessages],
  ["so-SO", soMessages],
  ["sq-AL", sqMessages],
  ["sr-RS", srMessages],
  ["sv-SE", svMessages],
  ["sw-TZ", swMessages],
  ["ta-IN", taMessages],
  ["te-IN", teMessages],
  ["th-TH", thMessages],
  ["tl", tlMessages],
  ["tr-TR", trMessages],
  ["uk-UA", ukMessages],
  ["ur", urMessages],
  ["vi-VN", viMessages],
  ["zh-CN", zhCNMessages],
  ["zh-HK", zhHKMessages],
  ["zh-TW", zhTWMessages],
]);
