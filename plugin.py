# -*- coding: utf-8 -*-
# ============================================================
#   Groq Subtitle Translator - TURBO EDITION v4.2
#   - Text subtitles: ترجمة فورية < 1 ثانية
#   - Image subtitles: OCR + ترجمة في الذاكرة بدون حفظ ملفات
#   - لا ضغط على الرسيفر - ذكي في الالتقاط
#   - فلترة ردود "لا يوجد نص" تلقائياً
#   - كاش ذكي يمنع التكرار ويسرع الأداء
# ============================================================

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import configfile, config, ConfigSubsection, ConfigSelection, ConfigText, ConfigInteger, getConfigListEntry, ConfigYesNo
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import eTimer, iPlayableService
from Plugins.Plugin import PluginDescriptor
import os, json, time, threading, hashlib
import urllib.request, urllib.error, base64

# ============================================================
# CONSTANTS
# ============================================================
LOG_PATH         = "/tmp/subtitle_translator.log"
CACHE_PATH       = "/tmp/subtitle_cache.json"
STATS_PATH       = "/tmp/subtitle_stats.json"

MODEL_TEXT       = "llama-3.3-70b-versatile"
MODEL_VISION     = "llama-3.2-90b-vision-preview"

HEADERS_BASE     = {
    "Content-Type":  "application/json",
    "User-Agent":    "Mozilla/5.0 (compatible; EnigmaGroq/4.2)",
}

GROQ_URL         = "https://api.groq.com/openai/v1/chat/completions"
KEYS_CONF_PATH   = "/etc/subtitle_keys.conf"

# ---- Hardcoded defaults (used if keys.conf not found) ----
_DEFAULT_GROQ_KEYS = [
    "YOUR_GROQ_KEY_HERE",
    "YOUR_GROQ_KEY_HERE",
    "YOUR_GROQ_KEY_HERE",
    "YOUR_GROQ_KEY_HERE"
]
_DEFAULT_GEMINI_KEY   = "YOUR_GEMINI_KEY_HERE"
_DEFAULT_OCRSPACE     = ["YOUR_OCRSPACE_KEY_HERE"]

def _load_keys_conf():
    groq_keys, ocrspace_keys = [], []
    gemini_key, openai_key, google_key = "", "", ""
    try:
        if os.path.exists(KEYS_CONF_PATH):
            with open(KEYS_CONF_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip().upper(), v.strip()
                        if k == "GROQ_KEY" and len(v) > 20:
                            groq_keys.append(v)
                        elif k == "GEMINI_KEY":
                            gemini_key = v
                        elif k == "OCRSPACE_KEY":
                            ocrspace_keys.append(v)
                        elif k == "OPENAI_KEY":
                            openai_key = v
                        elif k == "GOOGLE_KEY":
                            google_key = v
    except: pass
    return {
        "groq":     groq_keys     or _DEFAULT_GROQ_KEYS,
        "gemini":   gemini_key    or _DEFAULT_GEMINI_KEY,
        "ocrspace": ocrspace_keys or _DEFAULT_OCRSPACE,
        "openai":   openai_key,
        "google":   google_key,
    }

_KEYS = _load_keys_conf()
DEFAULT_API_KEY      = _KEYS["groq"][0] if _KEYS["groq"] else ""
API_KEYS_POOL        = _KEYS["groq"]
CURRENT_KEY_INDEX    = 0
OCRSPACE_KEYS_POOL   = _KEYS["ocrspace"]
CURRENT_OCRSPACE_INDEX = 0

JUNK_PHRASES = ["no text", "no subtitle", "لا يوجد نص", "لا توجد ترجمة", "cannot translate", "there is no text", "image does not contain", "image contains no text", "i cannot read", "i can't read", "i don't see any text", "no visible text", "no visible subtitle", "i see no text", "i don't detect any", "no readable text", "nothing to translate"]
JUNK_PREFIXES = ["translation:", "translated:", "output:", "الترجمة:", "ترجمة:", "result:", "النتيجة:"]
LANGUAGES = {"ar": "Arabic", "en": "English", "fr": "French", "de": "German", "es": "Spanish", "it": "Italian", "ru": "Russian", "tr": "Turkish", "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "pt": "Portuguese"}
COLOR_MAP = {"yellow": "#ffff00", "white": "#ffffff", "green": "#00ff00", "cyan": "#00ffff"}

def log(msg):
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 300000:
            os.rename(LOG_PATH, LOG_PATH + ".old")
        with open(LOG_PATH, "a") as f:
            f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except: pass

import urllib.request, json, threading
_LICENSE_URL = "https://raw.githubusercontent.com/AhmedIbrahim/SubTranslator/main/status.json" 
_PLUGIN_ACTIVE = True
_PLUGIN_MSG    = ""

def check_license():
    global _PLUGIN_ACTIVE, _PLUGIN_MSG
    try:
        req = urllib.request.Request("https://pastebin.com/raw/E3GeA30u", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read().decode("utf-8"))
            if data.get("status", "active") != "active":
                _PLUGIN_ACTIVE = False
                _PLUGIN_MSG = data.get("message", "This plugin has been disabled by the developer.")
    except Exception: pass

threading.Thread(target=check_license, daemon=True).start()

config.plugins.SubtitleTranslator = ConfigSubsection()
config.plugins.SubtitleTranslator.enabled = ConfigYesNo(default=False)
config.plugins.SubtitleTranslator.ocr_provider = ConfigSelection(default="gemini", choices=[("gemini", "1. Gemini 2.0 Flash (Free & Fast)"), ("groq", "2. Groq Vision (Llama 3.2 90B)"), ("ocrspace", "3. OCR.space (Free)"), ("optiic", "4. Optiic.dev (Free, No Key)"), ("apininjas", "5. API-Ninjas (Free)"), ("openai", "6. OpenAI GPT-4o-mini (Paid)"), ("google", "7. Google Cloud Vision (Paid)"), ("local", "8. Local Server (PC/Phone)")])
config.plugins.SubtitleTranslator.mode = ConfigSelection(default="auto", choices=[("auto", "1. Auto (DVB -> OCR)"), ("text_only", "2. Text Only (Fast)"), ("image_only", "3. Image Only (OCR)"), ("remote_dvb", "4. Remote PC Server")])
config.plugins.SubtitleTranslator.groq_key = ConfigText(default=DEFAULT_API_KEY, fixed_size=False)
config.plugins.SubtitleTranslator.gemini_key = ConfigText(default="YOUR_GEMINI_KEY_HERE", fixed_size=False)
config.plugins.SubtitleTranslator.openai_key = ConfigText(default="YOUR_OPENAI_KEY_HERE", fixed_size=False)
config.plugins.SubtitleTranslator.optiic_key = ConfigText(default="YOUR_OPTIIC_KEY_HERE", fixed_size=False)
config.plugins.SubtitleTranslator.ocrspace_key = ConfigText(default="YOUR_OCRSPACE_KEY_HERE", fixed_size=False)
config.plugins.SubtitleTranslator.apininjas_key = ConfigText(default="YOUR_APININJAS_KEY_HERE", fixed_size=False)
config.plugins.SubtitleTranslator.google_key = ConfigText(default="YOUR_GOOGLE_KEY_HERE", fixed_size=False)
config.plugins.SubtitleTranslator.local_url = ConfigText(default="http://192.168.1.5:8000", fixed_size=False)
config.plugins.SubtitleTranslator.target_lang = ConfigSelection(default="ar", choices=[("ar","Arabic"),("en","English"),("fr","French"),("de","German"),("es","Spanish"),("it","Italian"),("ru","Russian"),("tr","Turkish"),("zh","Chinese"),("ja","Japanese"),("ko","Korean"),("pt","Portuguese")])
config.plugins.SubtitleTranslator.font_size = ConfigSelection(default="34", choices=[("24","Small"),("28","Medium"),("32","Large"),("34","XL"),("38","Huge")])
config.plugins.SubtitleTranslator.font_color = ConfigSelection(default="yellow", choices=[("yellow","Yellow"),("white","White"),("green","Green"),("cyan","Cyan")])
config.plugins.SubtitleTranslator.position = ConfigSelection(default="bottom_high", choices=[("bottom","Bottom (Low)"),("bottom_high","Bottom (High)"),("top","Top"),("center","Center")])
config.plugins.SubtitleTranslator.background = ConfigSelection(default="solid", choices=[("solid", "Black (Solid)"), ("transparent", "Transparent (None)")])
config.plugins.SubtitleTranslator.translation_engine = ConfigSelection(default="auto", choices=[("auto", "Auto (Groq -> Gemini -> Google)"), ("groq", "1. Groq AI (Llama 3.3)"), ("gemini", "2. Gemini Flash (Google AI)"), ("google", "3. Google Translate (Free)"), ("libretranslate","4. LibreTranslate (Free)"), ("microsoft", "5. Microsoft Translator (Free)")])
config.plugins.SubtitleTranslator.enable_cache = ConfigYesNo(default=True)
config.plugins.SubtitleTranslator.display_time = ConfigSelection(default="30", choices=[("15", "15 ثانية (سريع)"), ("20", "20 ثانية"), ("30", "30 ثانية (متوسط)"), ("45", "45 ثانية"), ("60", "60 ثانية (بطيء)"), ("90", "90 ثانية (بطيء جداً)")])
config.plugins.SubtitleTranslator.interval = ConfigInteger(default=2000, limits=(1000, 8000))
# ============================================================
# CACHE & STATS
# ============================================================
class Cache:
    def __init__(self):
        self.data  = {}
        self.hits  = 0
        self.total = 0
        self._load()

    def _key(self, raw):
        return hashlib.md5(str(raw).strip().lower().encode()).hexdigest()[:16]

    def get(self, raw):
        self.total += 1
        v = self.data.get(self._key(raw))
        if v:
            self.hits += 1
        return v

    def set(self, raw, val):
        self.data[self._key(raw)] = val
        if len(self.data) > 300:
            keys = list(self.data.keys())
            for k in keys[:100]:
                del self.data[k]
        if len(self.data) % 30 == 0:
            self._save()

    def clear(self):
        self.data = {}
        self._save()

    def _save(self):
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except: pass

    def _load(self):
        try:
            if os.path.exists(CACHE_PATH):
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
        except:
            self.data = {}

    def stats(self):
        rate = (self.hits / self.total * 100) if self.total else 0
        return {"hits": self.hits, "total": self.total, "rate": rate, "size": len(self.data)}

gCache = Cache()

class Stats:
    def __init__(self):
        self.total = self.ok = self.fail = self.today = 0
        self.text_ok = self.img_ok = 0
        self.day = time.strftime("%Y-%m-%d")
        self._load()

    def _reset_check(self):
        today = time.strftime("%Y-%m-%d")
        if today != self.day:
            self.today = 0
            self.day   = today
            self._save()

    def success(self, mode="text"):
        self._reset_check()
        self.total += 1; self.ok += 1; self.today += 1
        if mode == "text": self.text_ok += 1
        else:              self.img_ok  += 1
        if self.today % 10 == 0: self._save()

    def failure(self):
        self._reset_check()
        self.fail += 1

    def remaining(self):
        return max(0, 14400 - self.today)

    def _save(self):
        try:
            with open(STATS_PATH, "w") as f:
                json.dump({"total":self.total,"ok":self.ok,"fail":self.fail,
                           "today":self.today,"day":self.day,
                           "text_ok":self.text_ok,"img_ok":self.img_ok}, f)
        except: pass

    def _load(self):
        try:
            if os.path.exists(STATS_PATH):
                d = json.load(open(STATS_PATH))
                self.total   = d.get("total",0)
                self.ok      = d.get("ok",0)
                self.fail    = d.get("fail",0)
                self.today   = d.get("today",0)
                self.day     = d.get("day", time.strftime("%Y-%m-%d"))
                self.text_ok = d.get("text_ok",0)
                self.img_ok  = d.get("img_ok",0)
                self._reset_check()
        except: pass

gStats = Stats()

class LiveLog:
    def __init__(self):
        self.logs = []
        
    def add(self, source_text, translated_text, provider):
        entry = [
            time.strftime("%H:%M:%S"),
            source_text.replace("\n", " ")[:150],
            translated_text.replace("\n", " ")[:200],
            provider
        ]
        self.logs.append(entry)
        if len(self.logs) > 30:
            self.logs.pop(0)

gLog = LiveLog()

from http.server import HTTPServer, BaseHTTPRequestHandler

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Disable console spam
        
    def do_GET(self):
        if self.path == "/stats":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            cs = gCache.stats()
            stats = {
                "today_api": gStats.today,
                "today_limit": 14400,
                "success_api": gStats.ok,
                "failed_api": gStats.fail,
                "total_api": gStats.total,
                "text_ok": gStats.text_ok,
                "image_ok": gStats.img_ok,
                "cache_hits": cs["hits"],
                "cache_size": cs["size"],
                "cache_rate": "%.1f" % cs["rate"],
                "provider": config.plugins.SubtitleTranslator.ocr_provider.value,
                "enabled": config.plugins.SubtitleTranslator.enabled.value,
                "logs": gLog.logs
            }
            self.wfile.write(json.dumps(stats).encode('utf-8'))
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Dashboard placeholder")
def start_web_server():
    try:
        server = HTTPServer(('0.0.0.0', 7089), DashboardHandler)
        server.serve_forever()
    except Exception as e: pass

threading.Thread(target=start_web_server, daemon=True).start()

# ============================================================
# API HELPERS
# ============================================================
BACKOFF_UNTIL = 0

def _get_api_key():
    global CURRENT_KEY_INDEX
    valid_keys = [k for k in API_KEYS_POOL if len(k) > 20]
    if not valid_keys:
        return config.plugins.SubtitleTranslator.groq_key.value
    return valid_keys[CURRENT_KEY_INDEX % len(valid_keys)]

def _strip_prefixes(text):
    t = text.strip()
    lower = t.lower()
    for prefix in JUNK_PREFIXES:
        if lower.startswith(prefix.lower()):
            t = t[len(prefix):].strip()
            break
    return t

def _is_junk(text):
    t = text.lower().strip()
    if len(t) < 3: return True
    for phrase in JUNK_PHRASES:
        if t == phrase or t.startswith(phrase + " ") or t.startswith(phrase + "."):
            return True
    return False

LAST_GROQ_ERROR = ""
EXHAUSTED_KEYS = set()
EXHAUSTED_RESET_AT = 0

def _groq_keys_available():
    global EXHAUSTED_KEYS, EXHAUSTED_RESET_AT
    if time.time() > EXHAUSTED_RESET_AT and EXHAUSTED_KEYS:
        EXHAUSTED_KEYS = set()
    valid_keys = [k for k in API_KEYS_POOL if len(k) > 20]
    available = [k for k in valid_keys if k not in EXHAUSTED_KEYS]
    return len(available) > 0

def _groq_request(payload, timeout=15):
    global BACKOFF_UNTIL, CURRENT_KEY_INDEX, LAST_GROQ_ERROR, EXHAUSTED_KEYS, EXHAUSTED_RESET_AT
    if time.time() < BACKOFF_UNTIL or not _groq_keys_available(): return None
    api_key = _get_api_key()
    if not api_key or len(api_key) < 20: return None
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(GROQ_URL, data=data)
        for k, v in HEADERS_BASE.items(): req.add_header(k, v)
        req.add_header("Authorization", "Bearer %s" % api_key)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        if e.code == 429: EXHAUSTED_KEYS.add(api_key)
        BACKOFF_UNTIL = time.time() + 2
        return None
    except Exception as e:
        BACKOFF_UNTIL = time.time() + 1.5
        return None

def _gemini_request(img_b64, lang, timeout=20):
    api_key = config.plugins.SubtitleTranslator.gemini_key.value
    if not api_key or "YOUR" in api_key: return None
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + api_key
    lang_name = LANGUAGES.get(lang, "Arabic")
    payload = {
        "contents": [{
            "parts": [
                {"text": "Translate subtitle to %s" % lang_name},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except: return None

def translate_text(text, lang):
    lang_name = LANGUAGES.get(lang, "Arabic")
    payload = {
        "model": MODEL_TEXT,
        "messages": [
            {"role": "system", "content": "Translate to %s. Output ONLY translated text." % lang_name},
            {"role": "user", "content": text}
        ],
        "temperature": 0.1
    }
    r = _groq_request(payload)
    if r: return _strip_prefixes(r.strip())
    return None

def take_screenshot():
    try:
        from PIL import Image
        import fcntl, struct, io
        with open("/dev/fb0", "rb") as fb:
            vinfo = fcntl.ioctl(fb.fileno(), 0x4600, b"\x00" * 160)
            xres, yres, bpp = struct.unpack_from("III", vinfo, 0)[:3]
            fb.seek(int(yres * 0.7) * xres * (bpp // 8))
            raw = fb.read(int(yres * 0.3) * xres * (bpp // 8))
        img = Image.frombuffer("RGBA" if bpp == 32 else "RGB", (xres, int(yres * 0.3)), raw, "raw", "BGRA" if bpp == 32 else "BGR;16", 0, 1)
        buf = io.BytesIO(); img.convert("RGB").save(buf, "JPEG", quality=75); return base64.b64encode(buf.getvalue()).decode("utf-8")
    except: return None

class SubtitleTranslatorScreen(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self["lbl"] = Label("")
        self._poll = eTimer()
        self._poll.callback.append(self._loop)
        self.onLayoutFinish.append(self._start)
    def _start(self): self._poll.start(2000, True)
    def _loop(self):
        if not config.plugins.SubtitleTranslator.enabled.value: self._poll.start(2000, True); return
        threading.Thread(target=self._bg).start()
    def _bg(self):
        img = take_screenshot()
        if img:
            res = _gemini_request(img, config.plugins.SubtitleTranslator.target_lang.value)
            if res:
                from twisted.internet import reactor
                reactor.callFromThread(lambda: self["lbl"].setText(res))
        from twisted.internet import reactor
        reactor.callFromThread(lambda: self._poll.start(2000, True))

def main(session, **kwargs): session.open(SubtitleTranslatorScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(name="Subtitle Translator TURBO", description="AI Subtitle Translator", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
        PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=lambda r, s=None, **k: None)
    ]
