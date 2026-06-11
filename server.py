# -*- coding: utf-8 -*-
"""ZHANGAI backend - single entry point.

Serves the web UI on :8080, launches llama-server as a child process
on :8090 (native web UI disabled), and routes all logs into this one
terminal. Also handles chat storage, skills, LLM proxying, web search
and user memory.

Conversations: chats/001/chat.json, chats/002/chat.json ...
Skills:        skills/*.py  (each defines SKILL dict + run(args) function)
No third-party packages required (Python 3.8+).
"""
import atexit
import html as html_mod
import http.client
import importlib.util
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "front"
CHATS_DIR = ROOT / "chats"
GEN_DIR = ROOT / "generated"
SKILLS_DIR = ROOT / "skills"
CHATS_DIR.mkdir(exist_ok=True)
GEN_DIR.mkdir(exist_ok=True)
SKILLS_DIR.mkdir(exist_ok=True)
PORT = 8080          # web UI + API (main page)
LLAMA_PORT = 8090    # llama-server (child process, no web UI)


def launch_llama():
    """Spawn llama-server as a child process; its logs share this terminal."""
    exe = os.environ.get("ZHANGAI_LLAMA", "")
    if not exe:
        for cand in (ROOT / "llama" / "llama-server.exe", ROOT / "llama" / "llama-server"):
            if cand.exists():
                exe = str(cand)
                break
    if not exe or not Path(exe).exists():
        print("  [llama] engine not found in llama/ - skipping launch (cloud providers still work)")
        return None
    model = os.environ.get("ZHANGAI_MODEL", str(ROOT / "model" / "main.gguf"))
    if not Path(model).exists():
        print(f"  [llama] model not found: {model} - skipping launch")
        return None
    mmproj = os.environ.get("ZHANGAI_MMPROJ", str(ROOT / "model" / "mmproj.gguf"))
    args = [exe, "-m", model,
            "-c", os.environ.get("ZHANGAI_CTX", "8192"),
            "-ngl", os.environ.get("ZHANGAI_NGL", "99"),
            "--port", str(LLAMA_PORT), "--host", "127.0.0.1", "--no-webui"]
    if Path(mmproj).exists():
        args += ["--mmproj", mmproj]
    extra = os.environ.get("ZHANGAI_LLAMA_ARGS", "")
    if extra:
        args += extra.split()
    print("  [llama] launching:", " ".join(args))
    proc = subprocess.Popen(args)   # inherits stdout/stderr -> single terminal
    atexit.register(lambda: proc.poll() is None and proc.terminate())
    return proc


# ════ skill loader: skills/*.py → SKILL + run() ════
def load_skills():
    sys.path.insert(0, str(SKILLS_DIR))
    out = []
    for f in sorted(SKILLS_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "SKILL") and hasattr(mod, "run"):
                out.append({**mod.SKILL, "fn": mod.run, "file": f.name})
                print(f"  [skill] {mod.SKILL['name']:<14} <- {f.name}")
            else:
                print(f"  [skip ] {f.name} (missing SKILL or run)")
        except Exception as e:
            print(f"  [error] {f.name}: {e}")
    return out


SKILLS = load_skills()
SKILL_MAP = {s["name"]: s for s in SKILLS}

# skills/skills.json 清單檔(AI 與前端直接讀這份)
(SKILLS_DIR / "skills.json").write_text(
    json.dumps([{k: s[k] for k in ("file", "name", "desc", "params")} for s in SKILLS],
               ensure_ascii=False, indent=2), encoding="utf-8")

# ════ 使用者記憶 memory.json ════
MEM_FILE = ROOT / "memory.json"


def read_mem():
    try:
        return json.loads(MEM_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"facts": []}


def write_mem(d):
    MEM_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


# ════ /search 網路搜尋:Selenium 無頭 Google → Bing → DuckDuckGo ════
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _http_get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")


_SEL = {"driver": None}
_SEL_LOCK = threading.Lock()


def _sel_driver():
    """常駐重用的無頭 Chrome(冷啟動 3-8 秒只付一次)。"""
    if _SEL["driver"] is not None:
        return _SEL["driver"]
    from selenium import webdriver                     # pip install selenium
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument("--headless=new")                # 不開視窗
    opts.add_argument("--disable-gpu")
    opts.add_argument("--log-level=3")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("user-agent=" + UA)
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    _SEL["driver"] = webdriver.Chrome(options=opts)    # Selenium Manager 自動抓 driver
    return _SEL["driver"]


def search_google_selenium(q, limit):
    from selenium.webdriver.common.by import By
    with _SEL_LOCK:
        for attempt in (1, 2):                         # driver 壞掉就重建一次
            try:
                driver = _sel_driver()
                driver.get("https://www.google.com/search?q="
                           + urllib.parse.quote(q) + "&num=10&hl=zh-TW")
                out = []
                for el in driver.find_elements(By.CSS_SELECTOR, "div.g"):
                    try:
                        a = el.find_element(By.CSS_SELECTOR, "a[href^='http']")
                        h3 = el.find_element(By.TAG_NAME, "h3")
                        lines = [ln for ln in el.text.split("\n") if len(ln) > 20]
                        snippet = lines[-1] if lines else ""
                        if h3.text.strip():
                            out.append({"title": h3.text.strip(),
                                        "url": a.get_attribute("href"),
                                        "snippet": snippet[:300]})
                    except Exception:
                        continue
                    if len(out) >= limit:
                        break
                return out
            except Exception:
                try:
                    _SEL["driver"].quit()
                except Exception:
                    pass
                _SEL["driver"] = None
                if attempt == 2:
                    raise


def search_bing(q, limit):
    page = _http_get("https://www.bing.com/search?q="
                     + urllib.parse.quote(q) + "&setlang=zh-hant")
    out = []
    for m in re.finditer(
            r'<li class="b_algo".*?<h2[^>]*><a[^>]+href="(http[^"]+)"[^>]*>(.*?)</a></h2>(.*?)</li>',
            page, re.S):
        url_, title = m.group(1), html_mod.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        sm = re.search(r"<p[^>]*>(.*?)</p>", m.group(3), re.S)
        snippet = html_mod.unescape(re.sub(r"<[^>]+>", "", sm.group(1))).strip() if sm else ""
        out.append({"title": title, "url": url_, "snippet": snippet[:300]})
        if len(out) >= limit:
            break
    return out


def search_ddg(q, limit):
    page = _http_get("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    titles = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                         page, re.S):
        href = m.group(1)
        title = html_mod.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        real = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0]
        titles.append({"title": title, "url": real})
    snips = [html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()
             for s in re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, re.S)]
    out = []
    for i, t in enumerate(titles[:limit]):
        t["snippet"] = snips[i] if i < len(snips) else ""
        out.append(t)
    return out


def page_text(url, max_chars=1800):
    """抓取網頁並抽出純文字內文。"""
    page = _http_get(url)
    page = re.sub(r"<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>",
                  " ", page, flags=re.S | re.I)
    # 優先取 <article> / <main>,沒有就整頁
    m = re.search(r"<(article|main)[^>]*>(.*?)</\1>", page, re.S | re.I)
    body = m.group(2) if m else page
    text = re.sub(r"<[^>]+>", " ", body)
    text = html_mod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def web_search(q, limit=6, deep=0):
    if not q.strip():
        return []
    errors = []
    out = []
    for name, fn in (("Google(Selenium)", search_google_selenium),
                     ("Bing", search_bing),
                     ("DuckDuckGo", search_ddg)):
        try:
            out = fn(q, limit)
            if out:
                print(f"  [search] {name} -> {len(out)} results")
                break
            errors.append(f"{name}: 0 results")
        except Exception as e:
            errors.append(f"{name}: {type(e).__name__} {e}")
    if not out:
        print("  [search] all engines failed:", " | ".join(errors))
        return [{"title": "Search failed - " + " | ".join(errors)[:400], "url": "", "snippet": ""}]
    for r in out[:deep]:
        try:
            r["content"] = page_text(r["url"])
            print(f"  [search] fetched {r['url'][:60]} ({len(r['content'])} chars)")
        except Exception as e:
            r["content"] = ""
            print(f"  [search] fetch failed {r['url'][:60]}: {e}")
    return out


# ════ LLM 上游(本地 / Gemini / DeepSeek,皆為 OpenAI 相容介面)════
LLM_UPSTREAMS = {
    "local":    (f"127.0.0.1:{LLAMA_PORT}", "/v1/chat/completions", False),
    "gemini":   ("generativelanguage.googleapis.com", "/v1beta/openai/chat/completions", True),
    "deepseek": ("api.deepseek.com", "/chat/completions", True),
}


def llm_once(provider, key, model, msgs, max_tokens=600, extra=None):
    """單次非串流 LLM 呼叫(後端內部用)。"""
    host, path, use_ssl = LLM_UPSTREAMS.get(provider, LLM_UPSTREAMS["local"])
    body = {"messages": msgs, "stream": False, "temperature": 0, "max_tokens": max_tokens}
    if model:
        body["model"] = model
    if extra:
        body.update(extra)
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    conn = (http.client.HTTPSConnection if use_ssl
            else http.client.HTTPConnection)(host, timeout=300)
    conn.request("POST", path, json.dumps(body).encode("utf-8"), headers)
    data = json.loads(conn.getresponse().read().decode("utf-8", "replace"))
    conn.close()
    return data.get("choices", [{}])[0].get("message", {})


MEM_SYS = ("你是記憶整理器。判斷對話中是否有「關於使用者本人」值得長期記住的【新】資訊"
           "(名字、身分、學校、工作、偏好、目標、設備、專案等)。"
           "我會給你已記住的清單:凡是意思已被清單涵蓋的(包括換句話說、縮寫、簡稱),一律不要再列。"
           "有新資訊的話每行一條,以「- 使用者」開頭;沒有新資訊就只輸出:無。只輸出清單,不要解釋。")

MEM_SYS_EN = ("You are a memory curator. Decide whether the conversation contains NEW long-term "
              "facts about the user (name, identity, school, job, preferences, goals, devices, "
              "projects). I will give you the list already memorized: skip anything the list "
              "already covers (including paraphrases and abbreviations). If there are new facts, "
              "output one per line starting with '- User'; if none, output only: NONE. "
              "Output the list only, no explanations.")


def _norm_fact(s):
    """正規化:去標點與常見贅詞,留語意核心。"""
    s = re.sub(r"[^\w一-鿿]", "", s)
    for w in ("使用者", "就讀於", "目前", "現在", "正在", "是一名", "是一位", "是", "的", "為", "在"):
        s = s.replace(w, "")
    return s


def _similar(a, b):
    """字元 bigram Jaccard 相似度 + 包含關係。"""
    na, nb = _norm_fact(a), _norm_fact(b)
    if not na or not nb:
        return False
    if na in nb or nb in na:
        return True
    A = {na[i:i+2] for i in range(max(1, len(na)-1))}
    B = {nb[i:i+2] for i in range(max(1, len(nb)-1))}
    return len(A & B) / max(1, len(A | B)) >= 0.5


FACT_PAT = r'^\s*[-•–]?\s*((?:使用者|User)[^`"「』{}\[\]<>\n]{2,100}?)\s*$'


def mem_extract(provider, key, model, user_text, ai_text, lang="zh"):
    noT = " /no_think" if provider == "local" else ""
    # Qwen3: hard-disable thinking via chat_template_kwargs so tokens go to the answer
    extra = {"chat_template_kwargs": {"enable_thinking": False}} if provider == "local" else None
    known = read_mem()["facts"]
    sys_p = MEM_SYS_EN if lang == "en" else MEM_SYS
    if lang == "en":
        known_txt = "\n".join("- " + f["text"] for f in known) or "(empty)"
        user_prompt = (f"Memorized list:\n{known_txt}\n\nConversation:\nUser said: {user_text[:800]}"
                       f"\nAI replied: {ai_text[:400]}\n\nOutput only NEW facts, or NONE.{noT}")
    else:
        known_txt = "\n".join("- " + f["text"] for f in known) or "(目前是空的)"
        user_prompt = (f"已記住的清單:\n{known_txt}\n\n對話內容:\n使用者說:{user_text[:800]}"
                       f"\nAI回:{ai_text[:400]}\n\n請只輸出清單上沒有的新資訊,或「無」。{noT}")
    try:
        msg = llm_once(provider, key, model,
                       [{"role": "system", "content": sys_p},
                        {"role": "user", "content": user_prompt}],
                       max_tokens=700, extra=extra)
    except Exception:
        # fallback for older llama-server builds without chat_template_kwargs
        msg = llm_once(provider, key, model,
                       [{"role": "system", "content": sys_p},
                        {"role": "user", "content": user_prompt}],
                       max_tokens=700)
    content = re.sub(r"<think>.*?</think>", " ", msg.get("content") or "", flags=re.S)
    reasoning = msg.get("reasoning_content") or ""
    print("  [memory] content:", content[:160].replace("\n", " | ") or "(empty)")
    if not content.strip():
        print("  [memory] reasoning tail:", reasoning[-160:].replace("\n", " | "))
    # 先解析正文;正文全空才用思考欄位,且只收純中文行(prompt 殘渣幾乎都夾英文)
    facts = [m.group(1).strip() for m in re.finditer(FACT_PAT, content, re.M)]
    if not facts and not content.strip():
        facts = [m.group(1).strip() for m in re.finditer(FACT_PAT, reasoning, re.M)
                 if lang == "en" or not re.search(r"[A-Za-z]", m.group(0))]
    if not facts:
        return 0, []
    mem = read_mem()
    added = 0
    for t in facts:
        dup = next((f["text"] for f in mem["facts"] if _similar(t, f["text"])), None)
        if dup:
            print(f"  [memory] duplicate, skipped: {t}  ~  {dup}")
            continue
        mem["facts"].append({"text": t, "time": time.strftime("%Y-%m-%d %H:%M")})
        added += 1
    if added:
        write_mem(mem)
    return added, facts


def next_chat_id() -> str:
    nums = [int(p.name) for p in CHATS_DIR.iterdir() if p.is_dir() and p.name.isdigit()]
    return f"{(max(nums) + 1) if nums else 1:03d}"


def chat_file(cid: str) -> Path:
    return CHATS_DIR / cid / "chat.json"


class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def match_chat(self):
        m = re.fullmatch(r"/api/chats/(\d{1,6})", self.path)
        return m.group(1) if m else None

    def serve_file(self, target: Path):
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")   # 禁止快取,避免舊版 JS 一直陰魂不散
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/chats":
            items = []
            for p in sorted(CHATS_DIR.iterdir(), reverse=True):
                f = p / "chat.json"
                if p.is_dir() and p.name.isdigit() and f.exists():
                    try:
                        d = json.loads(f.read_text(encoding="utf-8"))
                        items.append({"id": p.name, "title": d.get("title", p.name),
                                      "updated": d.get("updated", "")})
                    except Exception:
                        items.append({"id": p.name, "title": p.name, "updated": ""})
            return self.send_json(items)

        if self.path == "/api/skills":
            try:
                return self.send_json(json.loads(
                    (SKILLS_DIR / "skills.json").read_text(encoding="utf-8")))
            except Exception:
                return self.send_json([{k: s[k] for k in ("name", "desc", "params")} for s in SKILLS])

        if self.path == "/api/memory":
            return self.send_json(read_mem())

        if self.path.startswith("/api/search"):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            q = qs.get("q", [""])[0]
            deep = int(qs.get("deep", ["0"])[0] or 0)
            return self.send_json(web_search(q, deep=deep))

        if self.path.startswith("/api/fetch_page"):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            url = qs.get("url", [""])[0]
            try:
                return self.send_json({"ok": True, "content": page_text(url, 2200)})
            except Exception as e:
                return self.send_json({"ok": False, "content": "", "error": str(e)})

        cid = self.match_chat()
        if cid:
            f = chat_file(cid)
            if not f.exists():
                return self.send_json({"error": "not found"}, 404)
            return self.send_json(json.loads(f.read_text(encoding="utf-8")))

        rel = self.path.split("?")[0]
        if rel.startswith("/generated/"):
            target = (GEN_DIR / rel[len("/generated/"):]).resolve()
            if str(target).startswith(str(GEN_DIR.resolve())) and target.is_file():
                return self.serve_file(target)
            return self.send_json({"error": "not found"}, 404)

        rel = "index.html" if rel in ("/", "") else rel.lstrip("/")
        target = (UI_DIR / rel).resolve()
        if not str(target).startswith(str(UI_DIR.resolve())) or not target.is_file():
            return self.send_json({"error": "not found"}, 404)
        self.serve_file(target)

    def proxy_llm(self):
        body = self.read_body()
        provider = body.pop("provider", "local")
        key = body.pop("api_key", "")
        host, path, use_ssl = LLM_UPSTREAMS.get(provider, LLM_UPSTREAMS["local"])
        payload = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + key
        try:
            conn = (http.client.HTTPSConnection if use_ssl
                    else http.client.HTTPConnection)(host, timeout=600)
            conn.request("POST", path, payload, headers)
            resp = conn.getresponse()
        except Exception as e:
            return self.send_json(
                {"error": {"message": f"upstream connection failed ({provider}): {e}"}}, 502)
        self.send_response(resp.status)
        self.send_header("Content-Type", resp.getheader("Content-Type", "text/event-stream"))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        while True:
            try:
                # read1 = 有資料就立刻回傳,不等湊滿緩衝;否則低速生成會看起來像卡死
                chunk = resp.read1(8192) if hasattr(resp, "read1") else resp.read(256)
            except Exception:
                break
            if not chunk:
                break
            try:
                self.wfile.write(chunk)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                break
        conn.close()

    def do_POST(self):
        if self.path == "/api/llm":
            return self.proxy_llm()

        if self.path == "/api/mem_extract":
            b = self.read_body()
            try:
                added, facts = mem_extract(
                    b.get("provider", "local"), b.get("api_key", ""),
                    b.get("model", ""), b.get("user", ""), b.get("ai", ""),
                    b.get("lang", "zh"))
                return self.send_json({"ok": True, "added": added, "facts": facts})
            except Exception as e:
                return self.send_json({"ok": False, "error": str(e)})

        if self.path == "/api/memory":
            body = self.read_body()
            mem = read_mem()
            existing = {f["text"] for f in mem["facts"]}
            added = 0
            for t in body.get("facts", []):
                if not isinstance(t, str):
                    continue
                t = t.strip()
                # 入口防線:只收「使用者…」開頭的乾淨敘述,擋掉任何 prompt/思考殘渣
                if not re.fullmatch(r'(?:使用者|User)[^`"「』{}\[\]<>]{2,100}', t):
                    print("  [memory] rejected:", t[:80])
                    continue
                if t not in existing:
                    mem["facts"].append({"text": t,
                                         "time": time.strftime("%Y-%m-%d %H:%M")})
                    existing.add(t)
                    added += 1
            if added:
                write_mem(mem)
            return self.send_json({"ok": True, "count": len(mem["facts"]), "added": added})

        if self.path == "/api/chats":
            cid = next_chat_id()
            (CHATS_DIR / cid).mkdir(parents=True, exist_ok=True)
            chat_file(cid).write_text(
                json.dumps(self.read_body(), ensure_ascii=False, indent=2), encoding="utf-8")
            return self.send_json({"id": cid}, 201)

        if self.path == "/api/skills/run":
            body = self.read_body()
            name, args = body.get("name", ""), body.get("args", {}) or {}
            s = SKILL_MAP.get(name)
            if not s:
                return self.send_json({"ok": False, "text": f"unknown tool: {name}"})
            try:
                return self.send_json(s["fn"](args))
            except Exception as e:
                return self.send_json({"ok": False, "text": f"tool error: {e}"})

        self.send_json({"error": "bad route"}, 404)

    def do_PUT(self):
        cid = self.match_chat()
        if cid:
            (CHATS_DIR / cid).mkdir(parents=True, exist_ok=True)
            chat_file(cid).write_text(
                json.dumps(self.read_body(), ensure_ascii=False, indent=2), encoding="utf-8")
            return self.send_json({"ok": True})
        self.send_json({"error": "bad route"}, 404)

    def do_DELETE(self):
        if self.path == "/api/memory":
            write_mem({"facts": []})
            return self.send_json({"ok": True})
        cid = self.match_chat()
        if cid and (CHATS_DIR / cid).exists():
            shutil.rmtree(CHATS_DIR / cid, ignore_errors=True)
            return self.send_json({"ok": True})
        self.send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print()
    print("  ==========================================")
    print("    ZHANGAI  -  LOCAL AI CONSOLE")
    print("  ==========================================")
    print(f"    web UI : http://localhost:{PORT}")
    print(f"    engine : 127.0.0.1:{LLAMA_PORT} (native web UI disabled)")
    print(f"    chats  : {CHATS_DIR}")
    print(f"    skills : {len(SKILLS)} loaded")
    print("  ==========================================")
    print()
    launch_llama()
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n  [server] shutting down")
