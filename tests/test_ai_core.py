#!/usr/bin/env python3
"""Tests for bin/iram_ai_core.py and iram_voice.core pure helpers (no network, no Ollama)."""
import importlib.util
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_RUNTIME = tempfile.mkdtemp(prefix="iram-test-runtime-")
os.environ["XDG_RUNTIME_DIR"] = _RUNTIME  # keep the import-time circuit-breaker dir out of $HOME

spec = importlib.util.spec_from_file_location("iram_ai_core", os.path.join(REPO, "bin", "iram_ai_core.py"))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

sys.path.insert(0, REPO)
from iram_voice import core as voice  # noqa: E402


class CleanBashCommand(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(core.clean_bash_command(""), "")
        self.assertEqual(core.clean_bash_command(None), "")

    def test_fenced_block(self):
        self.assertEqual(core.clean_bash_command("Sure:\n```bash\nls -la\n```\nDone."), "ls -la")

    def test_inline_backticks(self):
        self.assertEqual(core.clean_bash_command("Run `df -h` now"), "df -h")

    def test_comments_and_prompt_marker(self):
        self.assertEqual(core.clean_bash_command("# list files\n$ ls"), "ls")

    def test_first_command_only(self):
        self.assertEqual(core.clean_bash_command("```sh\necho a\necho b\n```"), "echo a")


class Configuration(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        patcher = mock.patch.dict(os.environ, {"HOME": self.home}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL", "OLLAMA_MODEL", "IRAM_AI_PREFER_LOCAL"):
            os.environ.pop(var, None)

    def test_api_key_from_env(self):
        os.environ["GOOGLE_API_KEY"] = "abc"
        self.assertEqual(core.get_gemini_api_key(), "abc")

    def test_api_key_from_environment_d(self):
        d = os.path.join(self.home, ".config", "environment.d")
        os.makedirs(d)
        with open(os.path.join(d, "20-gemini.conf"), "w") as f:
            f.write('# c\nGEMINI_API_KEY="quoted-key"\n')
        self.assertEqual(core.get_gemini_api_key(), "quoted-key")

    def test_api_key_missing(self):
        self.assertEqual(core.get_gemini_api_key(), "")

    def test_tuned_models_and_defaults(self):
        d = os.path.join(self.home, ".config", "iram")
        os.makedirs(d)
        with open(os.path.join(d, "ai.env"), "w") as f:
            f.write("# tuned\nOLLAMA_MODEL=llama3:8b\n")
        self.assertEqual(core.get_tuned_models(), {"OLLAMA_MODEL": "llama3:8b"})
        self.assertEqual(core.get_default_models()[1], "llama3:8b")
        os.environ["OLLAMA_MODEL"] = "override"
        self.assertEqual(core.get_default_models()[1], "override")

    def test_default_ollama_model_without_tuning(self):
        self.assertEqual(core.get_default_models()[1], "qwen2.5:1.5b")

    def test_prefer_local_first(self):
        self.assertTrue(core.prefer_local_first())
        for off in ("0", "false", "no"):
            os.environ["IRAM_AI_PREFER_LOCAL"] = off
            self.assertFalse(core.prefer_local_first())
        os.environ["IRAM_AI_PREFER_LOCAL"] = " TRUE "
        self.assertTrue(core.prefer_local_first())


class CircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "breaker")
        for p in (mock.patch.object(core, "CIRCUIT_BREAKER_FILE", self.path),
                  mock.patch.object(core, "get_gemini_api_key", return_value="k")):
            p.start()
            self.addCleanup(p.stop)

    def test_healthy_without_marker(self):
        self.assertTrue(core.is_gemini_healthy())

    def test_unhealthy_without_key(self):
        with mock.patch.object(core, "get_gemini_api_key", return_value=""):
            self.assertFalse(core.is_gemini_healthy())

    def test_trips_then_recovers_after_cooldown(self):
        core.mark_gemini_failed("timeout")
        self.assertFalse(core.is_gemini_healthy())
        old = time.time() - core.CIRCUIT_COOLDOWN_SEC - 5
        os.utime(self.path, (old, old))
        self.assertTrue(core.is_gemini_healthy())
        self.assertFalse(os.path.exists(self.path))


class Hindsight(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        for p in (mock.patch.object(core, "DB_DIR", d),
                  mock.patch.object(core, "DB_PATH", os.path.join(d, "memory.db"))):
            p.start()
            self.addCleanup(p.stop)

    def test_retain_rejects_blank(self):
        self.assertIsNone(core.hindsight_retain("   "))

    def test_recall_empty_when_no_db(self):
        self.assertEqual(core.hindsight_recall("anything"), [])

    def test_retain_and_recall(self):
        core.hindsight_retain("user prefers tokyo storm theme", "prefs", 8)
        core.hindsight_retain("waybar restarts on failure", "system", 5)
        hits = core.hindsight_recall("tokyo theme")
        self.assertEqual([h["fact"] for h in hits], ["user prefers tokyo storm theme"])
        self.assertEqual(core.hindsight_recall("", category="SYSTEM")[0]["category"], "system")

    def test_recall_limit_and_punctuation_safe(self):
        for i in range(5):
            core.hindsight_retain(f"fact number {i}")
        self.assertEqual(len(core.hindsight_recall("fact", limit=2)), 2)
        self.assertIsInstance(core.hindsight_recall('fact" OR (*'), list)


class CondenseContext(unittest.TestCase):
    def test_short_text_unchanged(self):
        self.assertEqual(core.condense_context("a\nb", max_lines=5), "a\nb")

    def test_fallback_truncates_head_and_tail(self):
        text = "\n".join(f"line{i}" for i in range(100))
        with mock.patch.object(core.subprocess, "run", side_effect=FileNotFoundError):
            out = core.condense_context(text, max_lines=10)
        self.assertIn("line0", out)
        self.assertIn("line99", out)
        self.assertIn("90 lines condensed", out)
        self.assertNotIn("line50", out)


class VoiceFormat(unittest.TestCase):
    def test_format_from_path(self):
        self.assertEqual(voice.format_from_path("/tmp/a.WAV"), "wav")
        self.assertEqual(voice.format_from_path("a.ogg"), "opus")
        self.assertEqual(voice.format_from_path("a.m4a"), "aac")
        self.assertEqual(voice.format_from_path("noext"), "mp3")
        self.assertEqual(voice.format_from_path("a.unknown"), "mp3")


if __name__ == "__main__":
    unittest.main()
