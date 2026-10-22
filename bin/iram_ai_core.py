#!/usr/bin/env python3
"""
IRAM OS AI Core Engine & Circuit Breaker (iram_ai_core.py)
Unified, local-first inference dispatcher, circuit breaker, FTS5 Hindsight memory bridge,
and context condenser integration for all IRAM OS AI binaries.
https://github.com/apravint/iram-os
"""

import os
import sys
import json
import time
import re
import math
import sqlite3
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

def _get_circuit_breaker_file() -> str:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and os.path.isdir(runtime_dir):
        target_dir = os.path.join(runtime_dir, "iram")
    else:
        target_dir = os.path.expanduser("~/.local/state/iram")
    os.makedirs(target_dir, mode=0o700, exist_ok=True)
    return os.path.join(target_dir, "circuit_breaker_gemini_down")

CIRCUIT_BREAKER_FILE = _get_circuit_breaker_file()
CIRCUIT_COOLDOWN_SEC = 300  # 5 minutes before re-testing broken cloud endpoint

DB_DIR = os.path.expanduser("~/.local/share/iram/hindsight")
DB_PATH = os.path.join(DB_DIR, "memory.db")


# ==============================================================================
# 1. API Keys & Configuration
# ==============================================================================

def get_gemini_api_key() -> str:
    """Retrieves Google Gemini API key from environment or config files."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    env_file = os.path.expanduser("~/.config/environment.d/20-gemini.conf")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY=") or line.startswith("GOOGLE_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.exists(zshrc):
        try:
            with open(zshrc, "r") as f:
                for line in f:
                    if "GEMINI_API_KEY=" in line and not line.strip().startswith("#"):
                        val = line.split("GEMINI_API_KEY=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    return ""


def get_default_models() -> Tuple[str, str]:
    """Returns (gemini_model, ollama_model) with sensible fallbacks."""
    g_model = os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash"
    o_model = os.environ.get("OLLAMA_MODEL") or "qwen2.5:1.5b"
    return g_model, o_model


def prefer_local_first() -> bool:
    """Returns True if local Ollama should be prioritized (default on IRAM OS)."""
    pref = os.environ.get("IRAM_AI_PREFER_LOCAL", "1").strip().lower()
    return pref in ["1", "true", "yes", "on"]


# ==============================================================================
# 2. Fast Health Checks & Circuit Breaker
# ==============================================================================

def is_ollama_available(timeout: float = 0.5) -> bool:
    """Fast check whether local Ollama server is responsive."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_gemini_healthy() -> bool:
    """Checks circuit breaker. Returns False if recently timed out or missing key."""
    key = get_gemini_api_key()
    if not key:
        return False
    if os.path.exists(CIRCUIT_BREAKER_FILE):
        try:
            mtime = os.path.getmtime(CIRCUIT_BREAKER_FILE)
            if time.time() - mtime < CIRCUIT_COOLDOWN_SEC:
                return False  # Circuit open: cooldown active
            else:
                os.remove(CIRCUIT_BREAKER_FILE)
        except Exception:
            return False
    return True


def mark_gemini_failed(reason: str = ""):
    """Trips the circuit breaker to avoid further cloud timeouts."""
    try:
        with open(CIRCUIT_BREAKER_FILE, "w") as f:
            f.write(f"{time.time()}: {reason}\n")
    except Exception:
        pass


# ==============================================================================
# 3. Unified Inference Dispatcher
# ==============================================================================

def query_gemini_direct(prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, timeout: float = 6.0) -> Optional[str]:
    """Direct query to Google Gemini API with sensible timeout."""
    key = get_gemini_api_key()
    if not key:
        return None
    g_model = model or get_default_models()[0]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent"

    payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": key}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                if os.path.exists(CIRCUIT_BREAKER_FILE):
                    try:
                        os.remove(CIRCUIT_BREAKER_FILE)
                    except Exception:
                        pass
                return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        # Fallback to flash-lite if standard flash spikes
        if g_model != "gemini-3.5-flash-lite":
            try:
                fallback_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
                req_fallback = urllib.request.Request(
                    fallback_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "x-goog-api-key": key}
                )
                with urllib.request.urlopen(req_fallback, timeout=timeout) as resp_fallback:
                    data = json.loads(resp_fallback.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        if os.path.exists(CIRCUIT_BREAKER_FILE):
                            try:
                                os.remove(CIRCUIT_BREAKER_FILE)
                            except Exception:
                                pass
                        return candidates[0]["content"]["parts"][0]["text"].strip()
            except Exception:
                pass
        mark_gemini_failed(str(e))
    return None


def query_ollama_direct(prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, timeout: float = 20.0, num_predict: int = 256) -> Optional[str]:
    """Direct query to local Ollama server."""
    o_model = model or get_default_models()[1]
    url = "http://127.0.0.1:11434/api/generate"

    full_prompt = f"{system_prompt}\n\nTask: {prompt}" if system_prompt else prompt
    payload = {
        "model": o_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_predict": num_predict,
            "temperature": 0.2
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception:
        return None


def query_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    force_local: bool = False,
    num_predict: int = 256
) -> Tuple[str, str]:
    """
    Unified query function.
    Returns (response_text, provider_name).
    Prioritizes local Ollama for instantaneous zero-cost responses.
    """
    local_up = is_ollama_available(timeout=0.4)
    use_local_first = force_local or prefer_local_first() or not is_gemini_healthy()

    # Route 1: Local Ollama First
    if use_local_first and local_up:
        res = query_ollama_direct(prompt, system_prompt=system_prompt, model=model, num_predict=num_predict)
        if res:
            o_model = model or get_default_models()[1]
            return res, f"Ollama ({o_model})"

    # Route 2: Gemini Cloud Attempt (fast 2s timeout)
    if is_gemini_healthy():
        res = query_gemini_direct(prompt, system_prompt=system_prompt, model=model, timeout=2.0)
        if res:
            g_model = model or get_default_models()[0]
            return res, f"Gemini ({g_model})"

    # Route 3: Fallback back to Ollama if cloud failed
    if local_up:
        res = query_ollama_direct(prompt, system_prompt=system_prompt, model=model, num_predict=num_predict)
        if res:
            o_model = model or get_default_models()[1]
            return res, f"Ollama ({o_model})"

    return "", "None (All AI providers unavailable)"


# ==============================================================================
# 4. Command Output Cleaning & Sanitation
# ==============================================================================

def clean_bash_command(raw_text: str) -> str:
    """
    Strips markdown code blocks, backticks, comments, and leading prompts ($)
    so that only the raw executable bash command is returned.
    """
    if not raw_text:
        return ""
    text = raw_text.strip()

    # Extract block inside ```bash ... ``` or ``` ... ```
    match = re.search(r"```(?:bash|sh)?\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    else:
        # Match single-line code backticks `cmd`
        match_single = re.search(r"`([^`]+)`", text)
        if match_single:
            text = match_single.group(1).strip()

    # Split lines and extract first non-empty, non-comment line
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
    if lines:
        cmd = lines[0]
        # Remove leading '$ ' or '# ' prompt markers
        if cmd.startswith("$ ") or cmd.startswith("# "):
            cmd = cmd[2:].strip()
        return cmd
    return text.strip()


# ==============================================================================
# 5. Long-Term Memory (IRAM Hindsight Bridge)
# ==============================================================================

def init_hindsight_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        importance INTEGER DEFAULT 5,
        access_count INTEGER DEFAULT 0,
        created_at REAL,
        last_accessed REAL
    );
    """)
    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
        fact,
        category UNINDEXED,
        content='memories',
        content_rowid='id'
    );
    """)
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
      INSERT INTO memories_fts(rowid, fact, category) VALUES (new.id, new.fact, new.category);
    END;
    """)
    conn.commit()
    return conn


def hindsight_retain(fact: str, category: str = "general", importance: int = 5) -> Optional[int]:
    """Retains a fact or reflection into long-term SQLite FTS5 memory."""
    if not fact or not fact.strip():
        return None
    try:
        conn = init_hindsight_db()
        cur = conn.cursor()
        now = time.time()
        cur.execute(
            "INSERT INTO memories (fact, category, importance, access_count, created_at, last_accessed) VALUES (?, ?, ?, 1, ?, ?)",
            (fact.strip(), category.lower(), importance, now, now)
        )
        conn.commit()
        mem_id = cur.lastrowid
        conn.close()
        return mem_id
    except Exception:
        return None


def hindsight_recall(query: str = "", category: str = "", limit: int = 3) -> List[Dict[str, Any]]:
    """Recalls facts ranked by BM25 relevance and temporal recency decay."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = init_hindsight_db()
        cur = conn.cursor()
        now = time.time()

        query_clean = query.strip()
        if query_clean:
            words = re.findall(r'[a-zA-Z0-9_]+', query_clean)
            terms = [f'"{w}"' for w in words if len(w) > 1]
            fts_query = " OR ".join(terms) if terms else f'"{query_clean}"'
            sql = """
            SELECT m.id, m.fact, m.category, m.importance, m.access_count, m.created_at, m.last_accessed, bm25(memories_fts) as bm25_score
            FROM memories m
            JOIN memories_fts fts ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            """
            params = [fts_query]
            if category:
                sql += " AND m.category = ?"
                params.append(category.lower())
        else:
            sql = "SELECT id, fact, category, importance, access_count, created_at, last_accessed, 0.0 as bm25_score FROM memories"
            params = []
            if category:
                sql += " WHERE category = ?"
                params.append(category.lower())

        cur.execute(sql, params)
        rows = cur.fetchall()

        scored = []
        for r in rows:
            m_id, fact, cat, importance, acc_count, created_at, last_acc, bm25 = r
            age_hours = (now - last_acc) / 3600.0
            decay = math.exp(-0.005 * age_hours)
            total_score = (abs(bm25) * 1.5 if bm25 != 0 else 1.0) * (importance / 5.0) * decay
            scored.append({
                "id": m_id,
                "fact": fact,
                "category": cat,
                "importance": importance,
                "score": round(total_score, 3)
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[:limit]

        # Update access
        for item in results:
            cur.execute("UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?", (now, item["id"]))
        conn.commit()
        conn.close()
        return results
    except Exception:
        return []


# ==============================================================================
# 6. Context Condenser Bridge
# ==============================================================================

def condense_context(text: str, query: str = "", max_lines: int = 40) -> str:
    """Invokes iram-context-condenser to shrink large logs/diffs using BM25 with 0 LLM cost."""
    if not text or len(text.splitlines()) <= max_lines:
        return text
    try:
        cmd = ["iram-context-condenser", "-n", str(max_lines)]
        if query:
            cmd.extend(["-q", query])
        res = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    # Fallback to head/tail truncation
    lines = text.splitlines()
    half = max_lines // 2
    return "\n".join(lines[:half] + [f"\n... [{len(lines) - max_lines} lines condensed] ...\n"] + lines[-half:])
