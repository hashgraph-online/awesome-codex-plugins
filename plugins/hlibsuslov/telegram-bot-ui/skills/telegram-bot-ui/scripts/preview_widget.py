#!/usr/bin/env python3
"""Local preview of a Telegram HTML widget inside a MOCK of the widget runtime.

  py -3 scripts/preview_widget.py examples/widgets/metrics-dashboard.html -o preview.html
  py -3 scripts/preview_widget.py examples/widgets/src/slot-booking.html --lang ru -o p.html
  py -3 scripts/preview_widget.py examples/widgets/metrics-dashboard.html --serve 8765
  py -3 scripts/preview_widget.py --gallery -o gallery-preview.html     # every gallery widget

The page shows the widget in chat bubbles at several widths, with controls for the colour
scheme (light, dark, an outgoing bubble), right-to-left, the caption (below = no time band;
none = the time badge sits on the widget), the state (from examples/widgets/demo/NAME.json),
the place (private original, forward, inline preview, sent without allow_queries) and the
bot (answers, offline -> TIMEOUT, rate limited). Every request and answer is logged.

THIS IS A MOCK. A browser draws everything, including what Telegram apps remove; it enforces
none of the runtime limits except the few emulated here (one request in flight, a request
only in a tap or a permitted background call, 5 requests per 5 s, 600 px clip). A widget that
looks right here proves nothing about real clients: test in Telegram (see
references/widgets.md#testing).

Bot answers: with --serve, requests go to the gallery handler (examples/python/widget_gallery)
running in this process, with real state edits. Without it, answers are precomputed by the
same handler for the demo's "queries" from the selected state; other requests get bad_request.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "examples", "python"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_widget  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# Typical Telegram palettes for the mock (the real ones come from the user's chat theme).
THEMES = {
    "light": {"bg_color": "#ffffff", "text_color": "#000000", "hint_color": "#707579", "link_color": "#2481cc",
              "button_color": "#2481cc", "button_text_color": "#ffffff", "secondary_bg_color": "#f1f1f4",
              "accent_text_color": "#2481cc", "subtitle_text_color": "#707579", "destructive_text_color": "#e53935",
              "section_separator_color": "#e7e7ea", "section_bg_color": "#ffffff", "section_header_text_color": "#2481cc",
              "header_bg_color": "#ffffff", "bottom_bar_bg_color": "#ffffff", "_chat": "#c9d9b8", "_scheme": "light"},
    "dark": {"bg_color": "#212d3b", "text_color": "#ffffff", "hint_color": "#7d8b99", "link_color": "#62bcf9",
             "button_color": "#50a8eb", "button_text_color": "#ffffff", "secondary_bg_color": "#2b3a4b",
             "accent_text_color": "#64b5ef", "subtitle_text_color": "#7d8b99", "destructive_text_color": "#ee686f",
             "section_separator_color": "#0f161e", "section_bg_color": "#17212b", "section_header_text_color": "#6ab3f3",
             "header_bg_color": "#17212b", "bottom_bar_bg_color": "#17212b", "_chat": "#0e1621", "_scheme": "dark"},
    "outgoing": {"bg_color": "#effdde", "text_color": "#000000", "hint_color": "#5fa95a", "link_color": "#2d9c34",
                 "button_color": "#5fa95a", "button_text_color": "#ffffff", "secondary_bg_color": "#dcf5c6",
                 "accent_text_color": "#2d9c34", "subtitle_text_color": "#5fa95a", "destructive_text_color": "#d9534f",
                 "section_separator_color": "#c9e8b0", "section_bg_color": "#effdde", "section_header_text_color": "#2d9c34",
                 "header_bg_color": "#effdde", "bottom_bar_bg_color": "#effdde", "_chat": "#c9d9b8", "_scheme": "light"},
}
WIDTHS = [200, 320, 430, 600]

# The mock runtime, injected into each frame before the widget. Shape follows the stand-in of
# the Widgets guide ("A first look in a browser"), extended with events and request rules.
MOCK_JS = r"""
(function(){
var cfg = window.__cfg, P = parent, ev = {}, lastBg = 0, inFlight = false, stamps = [], tapUntil = 0;
function fire(t){ (ev[t]||[]).forEach(function(f){ try{ f.call(W); }catch(e){ P.postMessage({k:"log", f:cfg.f, t:"error", m:t+": "+e.message},"*"); } }); }
addEventListener("error", function(e){ P.postMessage({k:"log", f:cfg.f, t:"error", m:"uncaught: "+e.message},"*"); });
addEventListener("unhandledrejection", function(e){ P.postMessage({k:"log", f:cfg.f, t:"error", m:"unhandled rejection: "+(e.reason&&e.reason.message)},"*"); });
addEventListener("click", function(){ tapUntil = Date.now() + 50; }, true);
addEventListener("pointerup", function(){ tapUntil = Date.now() + 50; }, true);
try { Object.defineProperty(navigator, "language", {get:function(){ return cfg.lang; }}); } catch(e){}
window.fetch = function(){ throw new Error("NetworkDisabledError (mock)"); };
window.alert = window.confirm = window.prompt = function(){ P.postMessage({k:"log", f:cfg.f, t:"error", m:"dialogs are not shown in widgets"},"*"); return cfg.k==="confirm"?false:null; };
var W = window.TelegramWidget = {
  profile: 1, isProfileAtLeast: function(n){ return typeof n==="number" && n<=1; },
  colorScheme: cfg.scheme, themeParams: Object.freeze(cfg.theme), isActive: true,
  isPreview: cfg.place==="preview", isForward: cfg.place==="forward",
  chatType: cfg.place==="private" || cfg.place==="noqueries" ? "private" : null,
  viewer: cfg.place==="private" ? Object.freeze({id:111111111, first_name:"Alice", language_code:cfg.lang}) : null,
  chatData: cfg.place==="forward" ? null : cfg.chatData, publicData: cfg.publicData,
  wallet: null,
  contentSafeAreaInset: Object.freeze({top:0,right:0,left:0,bottom:cfg.band,cornerRight:cfg.dir==="rtl"?0:cfg.corner,cornerLeft:cfg.dir==="rtl"?cfg.corner:0}),
  HapticFeedback: { impactOccurred:function(){return this;}, notificationOccurred:function(t){ P.postMessage({k:"log",f:cfg.f,t:"haptic",m:t},"*"); return this;}, selectionChanged:function(){return this;} },
  onEvent: function(t,f){ (ev[t]=ev[t]||[]); if(ev[t].length<16) ev[t].push(f); },
  offEvent: function(t,f){ ev[t]=(ev[t]||[]).filter(function(g){return g!==f;}); },
  ready: function(){ P.postMessage({k:"ready", f:cfg.f, h:document.documentElement.scrollHeight},"*"); },
  setResizeAnchor: function(e){ if(e!=="top"&&e!=="bottom") throw new TypeError("edge"); },
  watchPublicData: function(){ P.postMessage({k:"log",f:cfg.f,t:"info",m:"watchPublicData()"},"*"); }, unwatchPublicData: function(){},
  openLink: function(u){ if(Date.now()>tapUntil) throw new Error("openLink outside a tap is refused"); if(!/^https:\/\//.test(u)||u.length>256) throw new TypeError("openLink: https URL up to 256 chars"); P.postMessage({k:"log",f:cfg.f,t:"link",m:"openLink "+u},"*"); },
  openTelegramLink: function(u){ if(Date.now()>tapUntil) throw new Error("openTelegramLink outside a tap is refused"); if(!/^https:\/\/t\.me\//.test(u)) throw new TypeError("openTelegramLink: https://t.me/ only"); P.postMessage({k:"log",f:cfg.f,t:"link",m:"openTelegramLink "+u},"*"); },
  copyText: function(t){ if(Date.now()>tapUntil) return; P.postMessage({k:"log",f:cfg.f,t:"copy",m:"copyText "+t},"*"); },
  request: function(data){
    if(typeof data!=="string" || !data || new TextEncoder().encode(data).length>64) throw new TypeError("request data: 1-64 bytes");
    var tap = Date.now() <= tapUntil, now = Date.now();
    function reject(code){ P.postMessage({k:"log",f:cfg.f,t:"reject",m:data+" -> "+code},"*"); var e=new Error(code); e.name="WidgetRequestError"; e.code=code; return Promise.reject(e); }
    if(cfg.place!=="private" && !(cfg.place==="forward" && cfg.shared && tap)) return reject("NOT_ALLOWED");
    if(!tap){ if(now-lastBg<5000) return reject("RATE_LIMITED"); lastBg = now; }
    if(inFlight) return reject("BUSY");
    stamps = stamps.filter(function(s){ return now-s<5000; });
    if(stamps.length>=5 || cfg.bot==="ratelimited") return reject("RATE_LIMITED");
    stamps.push(now); inFlight = true;
    var id = Math.random().toString(36).slice(2);
    return new Promise(function(res, rej){
      W.__pending[id] = function(m){ inFlight = false;
        if(m.code){ var e=new Error(m.code); e.name="WidgetRequestError"; e.code=m.code; rej(e); }
        else res(Object.freeze({result: m.result})); };
      P.postMessage({k:"req", f:cfg.f, id:id, data:data, tap:tap}, "*");
    });
  },
  __pending: {},
  __push: function(field, text){ if(cfg.place==="forward" && field==="chatData") return; W[field] = text; fire(field+"Changed"); },
  __answer: function(id, m){ var f = W.__pending[id]; delete W.__pending[id]; if(f) f(m); }
};
addEventListener("message", function(e){ if(e.source !== P) return; var m = e.data||{}; if(m.k==="ans") W.__answer(m.id, m); if(m.k==="push") W.__push(m.field, m.text); if(m.k==="theme") fire("themeChanged"); });
setInterval(function(){ P.postMessage({k:"size", f:cfg.f, h:document.documentElement.scrollHeight, n:document.getElementsByTagName("*").length},"*"); }, 500);
})();
"""

# The app's default stylesheet, approximated with zero specificity so any widget rule wins.
DEFAULT_CSS = """
:where(html){overflow:hidden;font:var(--tg-text-font-size)/var(--tg-text-line-height) system-ui,sans-serif;color:var(--tg-theme-text-color);
 color-scheme:var(--tg-color-scheme)}
:where(body){margin:8px 12px;padding-bottom:var(--tg-content-safe-area-inset-bottom)}
:where(button){background:var(--tg-button-bg);color:var(--tg-button-text);border:0;border-radius:var(--tg-button-radius);
 font:var(--tg-button-font);padding:var(--tg-button-padding);min-height:var(--tg-button-height)}
:where(button:active){opacity:.7}:where(button[disabled]){opacity:.5}
:where(h1,h2,h3,h4,p,ul,ol,table){margin:.4em 0}
"""

PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Widget preview (mock)</title>
<style>
:root{color-scheme:light dark;font:14px/1.4 system-ui,sans-serif}
body{margin:0;background:#e9edf1;color:#111}
header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid #ccd;padding:8px 12px}
.mock{background:#fff3cd;color:#5c4400;border:1px solid #e6c766;border-radius:6px;padding:6px 10px;margin-bottom:8px;font-weight:600}
.ctl{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center}
.ctl label{display:flex;gap:4px;align-items:center}
main{display:grid;grid-template-columns:1fr 340px;gap:12px;padding:12px}
@media (max-width:900px){main{grid-template-columns:1fr}}
.chat{border-radius:10px;padding:14px;display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start}
.cell{display:flex;flex-direction:column;gap:4px}
.cell .lbl{font-size:12px;color:#555;background:#fffd;border-radius:4px;padding:1px 6px;align-self:flex-start}
.bubble{position:relative;border-radius:14px;overflow:hidden;box-shadow:0 1px 2px #0003}
.bubble iframe{display:block;border:0;width:100%}
.cap{padding:6px 12px 8px;font:15px/1.35 system-ui,sans-serif;display:flex;gap:8px;justify-content:space-between}
.cap time{font-size:12px;opacity:.7;align-self:flex-end;white-space:nowrap}
.badge{position:absolute;bottom:4px;font:12px system-ui;color:#fff;background:#0007;border-radius:9px;padding:1px 7px}
.clip{position:absolute;left:0;right:0;bottom:0;height:3px;background:repeating-linear-gradient(90deg,#e53935 0 8px,transparent 8px 14px)}
.meta{font-size:12px;color:#555}
.meta.bad{color:#c62828;font-weight:600}
#log{background:#fff;border-radius:8px;padding:8px;font:12px/1.4 ui-monospace,monospace;height:70vh;overflow:auto;white-space:pre-wrap}
#log .req{color:#1565c0}#log .ans{color:#2e7d32}#log .reject,#log .error{color:#c62828}#log .push{color:#6a1b9a}
.side h3{margin:4px 0}
</style></head><body>
<header>
<div class="mock">MOCK runtime: a browser draws what Telegram apps remove and enforces almost none of their limits. This preview proves nothing about real clients.</div>
<div class="ctl">
<label>Widget <select id="wsel"></select></label>
<label>Scheme <select id="theme"><option>light</option><option>dark</option><option>outgoing</option></select></label>
<label><input type="checkbox" id="rtl"> RTL</label>
<label>Lang <select id="lang"></select></label>
<label>Caption <select id="cap"><option value="below">below</option><option value="none">none (time on widget)</option></select></label>
<label>State <select id="state"></select></label>
<label>Place <select id="place"><option value="private">private original</option><option value="noqueries">sent without allow_queries</option><option value="forward">forward</option><option value="preview">inline preview</option></select></label>
<label>Bot <select id="bot"><option value="answer">answers</option><option value="offline">offline (TIMEOUT)</option><option value="ratelimited">rate limited</option></select></label>
<label>Text <select id="fs"><option value="15">15px</option><option value="17">17px</option><option value="20">20px (large)</option></select></label>
<button id="reload">Reload</button>
</div></header>
<main><div id="chat" class="chat"></div>
<div class="side"><h3>Requests and state</h3><div id="log"></div></div></main>
<script>
var G = __GALLERY__, THEMES = __THEMES__, WIDTHS = __WIDTHS__, MOCK = __MOCK__, DEFCSS = __DEFCSS__, SERVE = __SERVE__;
var $ = function(i){ return document.getElementById(i); }, frames = {}, cur = null;
function opt(sel, values, val){ sel.innerHTML = ""; values.forEach(function(v){ var o=document.createElement("option"); o.textContent=v; sel.appendChild(o); }); if(val) sel.value = val; }
function log(t, m){ var d=document.createElement("div"); d.className=t; d.textContent=new Date().toLocaleTimeString()+" "+t+" "+m; $("log").prepend(d); }
function fresh(st, keys){ if(!st) return st; var s = JSON.parse(JSON.stringify(st)), now = Math.floor(Date.now()/1000), base = cur.demo.now || 0;
  (keys||[]).forEach(function(k){ if(typeof s[k]==="number" && base) s[k] = now - (base - s[k]); }); return s; }
function txt(v){ return v==null ? null : JSON.stringify(v); }
function render(){
  cur = G[$("wsel").value]; var d = cur.demo, th = THEMES[$("theme").value], rtl = $("rtl").checked;
  var langs = Object.keys(cur.html); if(langs.indexOf($("lang").value)<0) opt($("lang"), langs, langs[0]);
  var st = (d.states||{})[$("state").value] || {}, place = $("place").value, cap = $("cap").value;
  var vars = "--tg-color-scheme:"+th._scheme+";--tg-text-font-size:"+$("fs").value+"px;--tg-text-line-height:1.35;--tg-text-padding:8px 12px;"+
    "--tg-button-bg:"+th.button_color+";--tg-button-text:"+th.button_text_color+";--tg-button-radius:8px;--tg-button-font:500 "+$("fs").value+"px system-ui;--tg-button-padding:8px 12px;--tg-button-height:36px;--tg-button-pressed-opacity:.7;--tg-button-disabled-opacity:.5;";
  Object.keys(th).forEach(function(k){ if(k[0]!=="_") vars += "--tg-theme-"+k.replace(/_/g,"-")+":"+th[k]+";"; });
  var band = cap==="none" ? 22 : 0, corner = cap==="none" ? 58 : 0;
  vars += "--tg-content-safe-area-inset-bottom:"+band+"px;--tg-content-safe-area-inset-top:0px;--tg-content-safe-area-inset-left:0px;--tg-content-safe-area-inset-right:0px;"+
    "--tg-content-safe-area-corner-right:"+(rtl?0:corner)+"px;--tg-content-safe-area-corner-left:"+(rtl?corner:0)+"px;";
  var chat = $("chat"); chat.innerHTML = ""; chat.style.background = th._chat; frames = {};
  WIDTHS.forEach(function(w, i){
    var f = "f"+i, cfg = {f:f, scheme:th._scheme, theme:Object.assign({}, th), lang:$("lang").value, dir:rtl?"rtl":"ltr",
      place:place, shared:!!(d.send||{}).is_shared, bot:$("bot").value, band:band, corner:corner,
      chatData: txt(fresh(st.chatData, d.fresh)), publicData: txt(fresh(st.publicData, d.fresh))};
    delete cfg.theme._chat; delete cfg.theme._scheme;
    var cell = document.createElement("div"); cell.className = "cell";
    cell.innerHTML = '<span class="lbl">'+w+' px</span><div class="bubble" style="width:'+w+'px;background:'+th.bg_color+';color:'+th.text_color+'"><iframe scrolling="no"></iframe></div><span class="meta"></span>';
    var bubble = cell.querySelector(".bubble"), ifr = cell.querySelector("iframe");
    if(cap==="below"){ var c = document.createElement("div"); c.className = "cap"; c.innerHTML = "<span></span><time>10:00</time>"; c.firstChild.textContent = d.caption; bubble.appendChild(c); }
    else { var b = document.createElement("span"); b.className = "badge"; b.textContent = "10:00"; b.style[rtl?"left":"right"] = "6px"; bubble.appendChild(b); }
    var widget = cur.html[$("lang").value];
    ifr.srcdoc = '<!doctype html><html dir="'+cfg.dir+'" style="'+vars+'"><head><meta charset="utf-8"><style>'+DEFCSS+'</style><script>window.__cfg='+JSON.stringify(cfg)+';'+MOCK+'<\/script></head><body>'+widget+'</body></html>';
    frames[f] = {ifr:ifr, meta:cell.querySelector(".meta"), bubble:bubble, cfg:cfg, w:w};
    chat.appendChild(cell);
  });
  log("info", cur.name+" · "+$("state").value+" · "+place+" · "+$("theme").value+(rtl?" · rtl":"")+" · "+cur.sizes);
}
function setH(fr, h){ var shown = Math.max(50, Math.min(600, h)); fr.ifr.style.height = shown+"px";
  var clipped = h > 600; fr.meta.textContent = "content "+h+" px"+(clipped?" > 600: CLIPPED":"")+(fr.nodes?" · "+fr.nodes+" nodes":"");
  fr.meta.className = "meta"+(clipped||fr.nodes>2000?" bad":"");
  var cl = fr.bubble.querySelector(".clip"); if(clipped && !cl){ cl=document.createElement("div"); cl.className="clip"; fr.bubble.appendChild(cl); } if(!clipped && cl) cl.remove(); }
function answer(fr, m){
  var send = function(r){ fr.ifr.contentWindow.postMessage(Object.assign({k:"ans", id:m.id}, r), "*"); };
  log("req", fr.w+"px "+(m.tap?"tap":"background")+" "+m.data);
  if(fr.cfg.bot==="offline"){ setTimeout(function(){ log("reject", m.data+" -> TIMEOUT (15 s in Telegram, 2 s here)"); send({code:"TIMEOUT"}); }, 2000); return; }
  var done = function(res){
    (res.pushes||[]).forEach(function(p){ log("push", p.field+" r="+(JSON.parse(p.text||"{}").r)); fr.ifr.contentWindow.postMessage({k:"push", field:p.field, text:p.text}, "*"); });
    log("ans", (res.result||"null").slice(0,160)); send({result: res.result});
  };
  if(SERVE){ fetch("/q", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({widget:cur.name, data:m.data, frame:m.f, state:$("state").value})}).then(function(r){return r.json();}).then(function(res){ setTimeout(function(){ done(res); }, 250); }, function(){ send({code:"FAILED"}); }); return; }
  var pre = (cur.answers[$("state").value]||{})[m.data];
  setTimeout(function(){ done(pre || {result: JSON.stringify({ok:false, err:"bad_request", msg:"(mock) no precomputed answer: run with --serve"})}); }, 250);
}
// Any window may postMessage here: act only on the iframe registered under m.f.
addEventListener("message", function(e){ var m = e.data||{}, fr = frames[m.f]; if(!fr || e.source !== fr.ifr.contentWindow) return;
  if(m.k==="req") answer(fr, m);
  else if(m.k==="size"){ fr.nodes = m.n; setH(fr, m.h); }
  else if(m.k==="ready"){ setH(fr, m.h); }
  else if(m.k==="log") log(m.t, fr.w+"px "+m.m); });
opt($("wsel"), Object.keys(G));
function syncStates(){ opt($("state"), Object.keys(G[$("wsel").value].demo.states||{default:1}), "default"); var l = Object.keys(G[$("wsel").value].html); opt($("lang"), l, "en"); }
$("wsel").onchange = function(){ syncStates(); render(); };
["theme","rtl","lang","cap","state","place","bot","fs"].forEach(function(i){ $(i).onchange = render; });
$("reload").onclick = render;
syncStates(); render();
</script></body></html>"""


def widget_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def builds(path: str, langs: list[str] | None, design: dict | None = None) -> tuple[dict[str, str], str]:
    """{lang: html}. A source under src/ is built per language; a built file is used as is."""
    name = widget_name(path)
    src = os.path.join(build_widget.SRC_DIR, name + ".html")
    if os.path.exists(src):
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        out, sizes = {}, []
        for lang in langs or build_widget.source_languages(text):
            res = build_widget.build_text(text, caption="preview", langs=(lang,), design=design)
            if not res.ok:
                raise SystemExit(f"{name} [{lang}] does not build:\n  " + "\n  ".join(res.errors))
            out[lang] = res.html
            sizes.append(f"{lang} {res.compressed_bytes} B")
        return out, "zlib-9: " + ", ".join(sizes)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return {"en": text}, f"zlib-9: {build_widget.compressed_size(text)} B"


def precomputed_answers(name: str, demo: dict) -> dict:
    """Run the gallery handler offline for each demo query, from each demo state."""
    try:
        from tgkit.transport import FakeTransport
        from widget_gallery import SPECS, GalleryBot, query
    except ImportError:
        return {}
    if name not in SPECS:
        return {}
    out: dict = {}
    for state in demo.get("states", {}):
        out[state] = {}
        for i, data in enumerate(demo.get("queries", [])):
            t = FakeTransport()
            bot = GalleryBot(t)
            try:
                msg = bot.send(name, 111111111, state=state)
            except (ValueError, KeyError):
                continue
            upd = query(data, message_id=msg["message_id"], qid=f"p{i}",
                        widget_id=(msg.get("widget") or {}).get("id"))
            bot.handle(upd)
            bot.flush(1e12)
            out[state][data] = _result(t)
    return out


def _result(t) -> dict:
    pushes, result = [], None
    for method, params in t.calls[1:]:
        if method in ("editMessageWidgetData", "editSharedWidgetData"):
            for field, key in (("chatData", "chat_data"), ("publicData", "public_data")):
                if key in params:
                    pushes.append({"field": field, "text": params[key]})
        elif method == "answerWidgetQuery":
            result = params.get("data")
    return {"pushes": pushes, "result": result}


def gallery_entry(path: str, langs: list[str] | None, design: dict | None = None) -> dict:
    name = widget_name(path)
    demo_path = os.path.join(build_widget.DEMO_DIR, name + ".json")
    demo = build_widget.load_demo(demo_path) if os.path.exists(demo_path) else {
        "caption": name, "states": {"default": {}}}
    if "now" not in demo:
        demo["now"] = 1794736800
    html, sizes = builds(path, langs, design)
    return {"name": name, "demo": demo, "html": html, "sizes": sizes, "answers": precomputed_answers(name, demo)}


def page(entries: list[dict], serve: bool = False) -> str:
    gallery = {e["name"]: e for e in entries}
    rep = {"__GALLERY__": json.dumps(gallery, ensure_ascii=False), "__THEMES__": json.dumps(THEMES),
           "__WIDTHS__": json.dumps(WIDTHS), "__MOCK__": json.dumps(MOCK_JS), "__DEFCSS__": json.dumps(DEFAULT_CSS),
           "__SERVE__": "true" if serve else "false"}
    out = PAGE
    for k, v in rep.items():
        out = out.replace(k, v.replace("</", "<\\/"))
    return out


def rebased(demo: dict, state: str, field: str) -> dict | None:
    """The demo state with its "fresh" timestamps moved to now (as the page does)."""
    st = demo["states"].get(state, {}).get("chatData" if field == "chat_data" else "publicData")
    if not isinstance(st, dict):
        return st
    st, shift = dict(st), time.time() - demo.get("now", 1794736800)
    for k in demo.get("fresh", []):
        if isinstance(st.get(k), (int, float)):
            st[k] = int(st[k] + shift)
    return st


MAX_BODY = 1 << 20  # one widget query is a few hundred bytes
MAX_LIVE_BOTS = 256  # (widget, frame, state) bots kept; the oldest is dropped first


class _Live:
    """Per-widget live bots for --serve: real handler, real state transitions."""

    def __init__(self, entries: list[dict]):
        from tgkit.transport import FakeTransport
        from widget_gallery import SPECS, GalleryBot
        self.FakeTransport, self.GalleryBot, self.SPECS = FakeTransport, GalleryBot, SPECS
        self.bots: dict = {}
        self.lock = threading.Lock()
        self.n = 0

    def ask(self, body: dict) -> dict:
        from widget_gallery import query
        name, frame, state = body["widget"], body.get("frame", "f0"), body.get("state", "default")
        if name not in self.SPECS:
            return {"result": json.dumps({"ok": False, "err": "bad_request", "msg": "(mock) no handler"})}
        with self.lock:
            key = (name, frame, state)
            if key not in self.bots:
                t = self.FakeTransport()
                bot = self.GalleryBot(t, clock=time.time)
                spec = self.SPECS[name]
                msg = bot.send(name, 111111111, state=state,
                               state_override=rebased(spec.demo, state, spec.field))
                self.bots[key] = (t, bot, msg)
                while len(self.bots) > MAX_LIVE_BOTS:  # frame and state come from the page
                    del self.bots[next(iter(self.bots))]
            t, bot, msg = self.bots[key]
            self.n += 1
            mark = len(t.calls)
            bot.handle(query(body["data"], message_id=msg["message_id"], qid=f"s{self.n}",
                             widget_id=(msg.get("widget") or {}).get("id")))
            bot.flush(1e12)
            sub = self.FakeTransport()
            sub.calls = [("_", {})] + t.calls[mark:]
            return _result(sub)


def make_server(entries: list[dict], port: int) -> ThreadingHTTPServer:
    """The --serve server, same guards as the Studio: Host must be the loopback name and port
    it is bound to (DNS rebinding), a POST must come from that origin with a JSON body of at
    most MAX_BODY bytes, so another page in the browser can neither read nor drive it."""
    live = _Live(entries)
    html = page(entries, serve=True).encode("utf-8")

    class H(BaseHTTPRequestHandler):
        def _own(self) -> tuple[str, str]:
            port = self.server.server_address[1]
            return f"127.0.0.1:{port}", f"localhost:{port}"

        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _refuse(self, status: int, message: str) -> None:
            self.close_connection = True  # the unread body must not be parsed as the next request
            self._send(status, json.dumps({"error": message}).encode("utf-8"), "application/json")

        def do_GET(self):
            if self.headers.get("Host") not in self._own():
                return self._refuse(421, "unexpected Host")
            self._send(200, html, "text/html; charset=utf-8")

        def do_POST(self):
            if self.headers.get("Host") not in self._own():
                return self._refuse(421, "unexpected Host")
            if self.headers.get("Origin") not in tuple(f"http://{h}" for h in self._own()):
                return self._refuse(403, "cross-origin request")
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._refuse(415, "Content-Type must be application/json")
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._refuse(400, "bad Content-Length")
            if not 0 <= n <= MAX_BODY:
                return self._refuse(413, f"body over {MAX_BODY} bytes")
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._refuse(400, "body is not JSON")
            if not (isinstance(body, dict) and isinstance(body.get("widget"), str)
                    and isinstance(body.get("data"), str)
                    and all(isinstance(body.get(k, ""), str) for k in ("frame", "state"))):
                return self._refuse(400, "expected {widget, data, frame?, state?} strings")
            self._send(200, json.dumps(live.ask(body)).encode("utf-8"), "application/json")

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), H)


def serve(entries: list[dict], port: int) -> None:
    srv = make_server(entries, port)
    print(f"preview (MOCK runtime) on http://127.0.0.1:{port}/  - Ctrl+C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("widget", nargs="*", help="built widget (examples/widgets/NAME.html) or its source")
    ap.add_argument("--gallery", action="store_true", help="every widget with a demo file")
    ap.add_argument("--lang", help="comma-separated languages to build (sources only)")
    ap.add_argument("-o", "--out", help="write the preview page here")
    ap.add_argument("--design", help="design profile JSON or a preset name (scripts/widget_design.py presets)")
    ap.add_argument("--serve", type=int, metavar="PORT", help="serve the page and answer with the gallery handlers")
    a = ap.parse_args(argv)
    paths = list(a.widget)
    if a.gallery:
        paths += [os.path.join(build_widget.OUT_DIR, n) for n in build_widget.gallery_sources()]
    if not paths:
        ap.error("give a widget file or --gallery")
    langs = a.lang.split(",") if a.lang else None
    design = None
    if a.design:
        import widget_design
        design = (widget_design.apply_preset(a.design) if a.design in widget_design.PRESETS
                  else build_widget.load_demo(a.design))
    entries = [gallery_entry(p, langs, design) for p in paths]
    if a.serve:
        serve(entries, a.serve)
        return 0
    out = a.out or os.path.join(os.getcwd(), "widget-preview.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page(entries))
    print(f"wrote {out} (MOCK runtime: proves nothing about real clients); "
          + "; ".join(f"{e['name']} {e['sizes']}" for e in entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
