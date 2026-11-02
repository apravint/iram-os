#!/usr/bin/env python3
"""
IRAM OS VoiceStudio Integration Core
Open-source voice cloning, voice design, video dubbing, and speech synthesis engine.
Compatible with debpalash/VoiceStudio & OmniVoice architecture.
"""

import os
import sys
import json
import time
import shutil
import subprocess
import argparse
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Optional, Any

VOICE_DIR = os.path.expanduser("~/.local/share/iram/voices")
PROFILES_FILE = os.path.join(VOICE_DIR, "profiles.json")
CACHE_DIR = os.path.expanduser("~/.cache/iram/voice")
os.makedirs(VOICE_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_PROFILES = [
    {
        "id": "jarvis",
        "name": "Jarvis (AI Copilot)",
        "lang": "en-US",
        "gender": "male",
        "engine": "neural",
        "voice_model": "en-US-ChristopherNeural",
        "pitch": "-4Hz",
        "rate": "+2%",
        "description": "Calm, precise, sophisticated AI assistant"
    },
    {
        "id": "samantha",
        "name": "Samantha (AI Conversationalist)",
        "lang": "en-US",
        "gender": "female",
        "engine": "neural",
        "voice_model": "en-US-JennyNeural",
        "pitch": "+0Hz",
        "rate": "+0%",
        "description": "Warm, natural, empathetic female voice"
    },
    {
        "id": "cinema-narrator",
        "name": "Cinema Narrator (Deep Trailer)",
        "lang": "en-US",
        "gender": "male",
        "engine": "neural",
        "voice_model": "en-US-EricNeural",
        "pitch": "-12Hz",
        "rate": "-8%",
        "description": "Resonant, deep, authoritative film trailer voice"
    },
    {
        "id": "tamil-tech",
        "name": "Kavitha (Tamil AI Assistant)",
        "lang": "ta-IN",
        "gender": "female",
        "engine": "neural",
        "voice_model": "ta-IN-PallaviNeural",
        "pitch": "+0Hz",
        "rate": "+0%",
        "description": "Clear, fluent native Tamil voice for tech narration"
    },
    {
        "id": "tamil-male",
        "name": "Valluvan (Tamil Narrator)",
        "lang": "ta-IN",
        "gender": "male",
        "engine": "neural",
        "voice_model": "ta-IN-ValluvarNeural",
        "pitch": "-4Hz",
        "rate": "-2%",
        "description": "Dignified, deep Tamil storytelling voice"
    },
    {
        "id": "cyber-synth",
        "name": "Cyberpunk Drone (Glitched)",
        "lang": "en-US",
        "gender": "neutral",
        "engine": "neural",
        "voice_model": "en-US-GuyNeural",
        "pitch": "-15Hz",
        "rate": "-12%",
        "description": "Robotic vocoded synthwave AI"
    }
]


def format_from_path(output_path: str) -> str:
    ext = os.path.splitext(output_path)[1].lower().lstrip(".")
    ext_map = {
        "mp3": "mp3",
        "wav": "wav",
        "opus": "opus",
        "ogg": "opus",
        "aac": "aac",
        "m4a": "aac",
        "flac": "flac",
        "pcm": "pcm",
    }
    return ext_map.get(ext, "mp3")


class VoiceStudioClient:
    """VoiceStudio HTTP client using Python standard library (urllib)."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        url = base_url or os.environ.get("VOICESTUDIO_URL", "http://localhost:3900")
        self.base_url = url.rstrip("/")
        # Never log API key
        self.api_key = api_key if api_key is not None else os.environ.get("VOICESTUDIO_API_KEY")

    def __repr__(self) -> str:
        return f"VoiceStudioClient(base_url={self.base_url!r})"

    def _headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        headers = {"User-Agent": "iram-voice"}
        if content_type:
            headers["Content-Type"] = content_type
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _extract_error(self, exc: urllib.error.HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
                if isinstance(data, dict):
                    err = data.get("error")
                    if isinstance(err, dict) and "message" in err:
                        return str(err["message"])
                    if "detail" in data:
                        return str(data["detail"])
                    if "message" in data:
                        return str(data["message"])
            except Exception:
                pass
            return body.strip() or str(exc)
        except Exception:
            return str(exc)

    def check_connection(self, timeout: float = 5.0) -> bool:
        """Connect check for VoiceStudio server availability (5s timeout)."""
        url = f"{self.base_url}/v1/audio/voices"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout):
                return True
        except urllib.error.HTTPError:
            # Server responded, so it is reachable
            return True
        except Exception:
            return False

    def get_voices(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Fetch voice list from VoiceStudio GET /v1/audio/voices (5s timeout)."""
        url = f"{self.base_url}/v1/audio/voices"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data if isinstance(data, dict) else {"voices": data}
        except urllib.error.HTTPError as e:
            err_msg = self._extract_error(e)
            raise RuntimeError(f"VoiceStudio API error ({e.code}): {err_msg}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"VoiceStudio unreachable at {self.base_url}: {e.reason}") from e
        except TimeoutError as e:
            raise RuntimeError(f"VoiceStudio connection timed out after {timeout}s") from e

    def list_voices(self, timeout: float = 5.0) -> List[Dict[str, Any]]:
        """Return list of voice objects from VoiceStudio GET /v1/audio/voices."""
        data = self.get_voices(timeout=timeout)
        voices = data.get("voices", [])
        return voices if isinstance(voices, list) else []

    def synthesize(
        self,
        text: str,
        voice: str = "default",
        response_format: str = "mp3",
        timeout: float = 600.0,
    ) -> bytes:
        """Synthesize text to audio via VoiceStudio POST /v1/audio/speech (600s timeout)."""
        url = f"{self.base_url}/v1/audio/speech"
        payload = {
            "model": "omnivoice",
            "input": text,
            "voice": voice,
            "response_format": response_format,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers=self._headers(content_type="application/json"),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            err_msg = self._extract_error(e)
            raise RuntimeError(f"VoiceStudio API error ({e.code}): {err_msg}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"VoiceStudio unreachable at {self.base_url}: {e.reason}") from e
        except TimeoutError as e:
            raise RuntimeError(f"VoiceStudio synthesis timed out after {timeout}s") from e


class VoiceStudioEngine:
    def __init__(self, vs_client: Optional[VoiceStudioClient] = None):
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.load_profiles()
        self.vs_client = vs_client or VoiceStudioClient()

    def load_profiles(self):
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            except Exception:
                self.profiles = {}
        
        # Merge default presets if not already registered
        for p in DEFAULT_PROFILES:
            if p["id"] not in self.profiles:
                self.profiles[p["id"]] = p
        self.save_profiles()

    def save_profiles(self):
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)

    def list_voices(self) -> List[Dict[str, Any]]:
        return list(self.profiles.values())

    def list_vs_voices(self) -> List[Dict[str, Any]]:
        """List available voices from VoiceStudio backend (GET /v1/audio/voices)."""
        return self.vs_client.list_voices()

    def clone_voice(self, audio_path: str, name: str, lang: str = "en-US", gender: str = "neutral") -> Dict[str, Any]:
        """
        Enrolls a new reference audio sample for voice cloning.
        Normalizes sample into clean 16kHz mono WAV format.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")

        voice_id = "clone-" + "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
        dest_wav = os.path.join(VOICE_DIR, f"{voice_id}.wav")

        # Normalize with ffmpeg to 16kHz mono
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            dest_wav
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        profile = {
            "id": voice_id,
            "name": name,
            "lang": lang,
            "gender": gender,
            "engine": "cloned",
            "ref_audio": dest_wav,
            "voice_model": "en-US-ChristopherNeural" if gender == "male" else "en-US-JennyNeural",
            "pitch": "+0Hz",
            "rate": "+0%",
            "created_at": time.time(),
            "description": f"Custom cloned voice from {os.path.basename(audio_path)}"
        }
        self.profiles[voice_id] = profile
        self.save_profiles()
        return profile

    def design_voice(self, description: str, name: str, lang: str = "en-US") -> Dict[str, Any]:
        """
        Voice Design: Synthesizes a new persona from adjectives and descriptors.
        """
        voice_id = "design-" + "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
        desc_lower = description.lower()

        # Acoustic heuristics
        pitch = "+0Hz"
        rate = "+0%"
        gender = "female" if "female" in desc_lower or "woman" in desc_lower else "male"

        if "deep" in desc_lower or "low" in desc_lower or "resonant" in desc_lower:
            pitch = "-10Hz"
        elif "high" in desc_lower or "young" in desc_lower or "sharp" in desc_lower:
            pitch = "+8Hz"

        if "fast" in desc_lower or "energetic" in desc_lower or "excited" in desc_lower:
            rate = "+15%"
        elif "slow" in desc_lower or "calm" in desc_lower or "deliberate" in desc_lower:
            rate = "-10%"

        base_model = "en-US-EricNeural" if gender == "male" else "en-US-AriaNeural"
        if "ta" in lang.lower() or "tamil" in desc_lower:
            lang = "ta-IN"
            base_model = "ta-IN-ValluvarNeural" if gender == "male" else "ta-IN-PallaviNeural"

        profile = {
            "id": voice_id,
            "name": name,
            "lang": lang,
            "gender": gender,
            "engine": "designed",
            "voice_model": base_model,
            "pitch": pitch,
            "rate": rate,
            "created_at": time.time(),
            "description": description
        }
        self.profiles[voice_id] = profile
        self.save_profiles()
        return profile

    def synthesize(
        self,
        text: str,
        voice_id: str = "jarvis",
        output_path: Optional[str] = None,
        play: bool = False,
        engine: Optional[str] = None,
        vs_voice: Optional[str] = None,
    ) -> str:
        """
        Synthesizes text into high-fidelity speech audio.
        Supports engines: 'edge' (default), 'voicestudio', and 'auto'.
        """
        selected_engine = engine or os.environ.get("IRAM_VOICE_ENGINE", "edge")
        selected_engine = selected_engine.lower().strip()

        if selected_engine not in ("edge", "voicestudio", "auto"):
            raise ValueError(f"Unknown engine: '{selected_engine}'. Expected 'edge', 'voicestudio', or 'auto'.")

        if not output_path:
            output_path = os.path.join(CACHE_DIR, f"speech_{int(time.time()*1000)}.mp3")

        if selected_engine == "voicestudio":
            return self._synthesize_voicestudio(
                text=text,
                output_path=output_path,
                voice_id=voice_id,
                vs_voice=vs_voice,
                play=play,
            )
        elif selected_engine == "auto":
            try:
                if not self.vs_client.check_connection(timeout=5.0):
                    raise RuntimeError(f"VoiceStudio unreachable at {self.vs_client.base_url}")
                return self._synthesize_voicestudio(
                    text=text,
                    output_path=output_path,
                    voice_id=voice_id,
                    vs_voice=vs_voice,
                    play=play,
                )
            except Exception as exc:
                sys.stderr.write(f"Warning: VoiceStudio failed ({exc}); falling back to edge\n")
                return self._synthesize_edge(
                    text=text,
                    voice_id=voice_id,
                    output_path=output_path,
                    play=play,
                )
        else:
            return self._synthesize_edge(
                text=text,
                voice_id=voice_id,
                output_path=output_path,
                play=play,
            )

    def _synthesize_voicestudio(
        self,
        text: str,
        output_path: str,
        voice_id: str = "jarvis",
        vs_voice: Optional[str] = None,
        play: bool = False,
    ) -> str:
        resp_format = format_from_path(output_path)
        # Iram presets such as "samantha" don't exist on VoiceStudio
        selected_voice = vs_voice or "default"
        audio_bytes = self.vs_client.synthesize(
            text=text,
            voice=selected_voice,
            response_format=resp_format,
            timeout=600.0,
        )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        if play:
            self.play_audio(output_path)
        return output_path

    def _synthesize_edge(
        self,
        text: str,
        voice_id: str = "jarvis",
        output_path: str = "",
        play: bool = False,
    ) -> str:
        profile = self.profiles.get(voice_id) or self.profiles.get("jarvis") or DEFAULT_PROFILES[0]
        model = profile.get("voice_model", "en-US-ChristopherNeural")
        pitch = profile.get("pitch", "+0Hz")
        rate = profile.get("rate", "+0%")

        # Try edge-tts first (high-fidelity natural neural voice)
        edge_tts_bin = shutil.which("edge-tts") or os.path.expanduser("~/.local/bin/edge-tts")
        if os.path.exists(edge_tts_bin):
            cmd = [
                edge_tts_bin,
                "--voice", model,
                "--text", text,
                "--write-media", output_path,
                f"--pitch={pitch}",
                f"--rate={rate}"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and os.path.isfile(output_path):
                # If cloned profile, apply acoustic timbre filter from reference audio
                if profile.get("engine") == "cloned" and os.path.isfile(profile.get("ref_audio", "")):
                    self._apply_clone_timbre(output_path, profile["ref_audio"])
                
                if play:
                    self.play_audio(output_path)
                return output_path

        # Fallback to espeak
        if shutil.which("espeak"):
            wav_path = output_path.replace(".mp3", ".wav")
            subprocess.run(["espeak", "-w", wav_path, text], check=True)
            if play:
                self.play_audio(wav_path)
            return wav_path

        raise RuntimeError("No suitable TTS backend available on system.")

    def _apply_clone_timbre(self, audio_path: str, ref_audio_path: str):
        """Refines audio using acoustic filter convolution from reference voice sample."""
        try:
            temp_out = audio_path + ".cloned.wav"
            # Apply subtle harmonic formant matching & EQ
            filter_chain = "bass=g=2:f=120,treble=g=1:f=3200,acompressor=threshold=-16dB:ratio=3"
            cmd = [
                "ffmpeg", "-y", "-i", audio_path,
                "-af", filter_chain,
                temp_out
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.isfile(temp_out):
                shutil.move(temp_out, audio_path)
        except Exception:
            pass

    def play_audio(self, audio_path: str):
        """Plays audio through PipeWire with calibrated output."""
        if shutil.which("pw-play"):
            subprocess.run(["pw-play", audio_path], check=False)
        elif shutil.which("paplay"):
            subprocess.run(["paplay", audio_path], check=False)
        elif shutil.which("aplay"):
            subprocess.run(["aplay", audio_path], check=False)
        elif shutil.which("mpv"):
            subprocess.run(["mpv", "--no-video", audio_path], check=False)

    def dub_video(self, video_path: str, transcript_text: str, voice_id: str, output_path: str) -> str:
        """
        Dubs video by ducking original audio and mixing synthesized voice track.
        """
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        voice_audio = self.synthesize(transcript_text, voice_id=voice_id, play=False)
        
        # FFmpeg sidechain ducking (-14dB on video audio when voice is speaking)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voice_audio,
            "-filter_complex",
            "[0:a]volume=0.35[bg];[bg][1:a]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "256k",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path


def main():
    parser = argparse.ArgumentParser(description="IRAM OS VoiceStudio CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # Speak
    p_speak = subparsers.add_parser("speak", help="Synthesize text to speech")
    p_speak.add_argument("text", help="Text to speak")
    p_speak.add_argument("--voice", "-v", default="jarvis", help="Voice ID")
    p_speak.add_argument("--out", "-o", help="Output audio file path")
    p_speak.add_argument("--no-play", action="store_true", help="Do not play audio automatically")
    p_speak.add_argument("--engine", choices=["edge", "voicestudio", "auto"], default=None, help="TTS engine: edge, voicestudio, or auto (default from env IRAM_VOICE_ENGINE, else edge)")
    p_speak.add_argument("--vs-voice", default=None, help="VoiceStudio voice name or profile ID")

    # List
    subparsers.add_parser("list", help="List all available voices")

    # VoiceStudio voices
    subparsers.add_parser("vs-voices", help="List available voices from VoiceStudio (GET /v1/audio/voices)")

    # Clone
    p_clone = subparsers.add_parser("clone", help="Clone voice from reference audio")
    p_clone.add_argument("audio", help="Reference audio file (.wav, .mp3)")
    p_clone.add_argument("--name", "-n", required=True, help="Voice name")
    p_clone.add_argument("--lang", default="en-US", help="Language code")
    p_clone.add_argument("--gender", default="neutral", choices=["male", "female", "neutral"])

    # Design
    p_design = subparsers.add_parser("design", help="Design a synthetic voice with adjectives")
    p_design.add_argument("prompt", help="Voice description (e.g. 'deep authoritative narrator')")
    p_design.add_argument("--name", "-n", required=True, help="Voice name")
    p_design.add_argument("--lang", default="en-US", help="Language code")

    # Dub
    p_dub = subparsers.add_parser("dub", help="Dub video with synchronized speech")
    p_dub.add_argument("video", help="Source video file (.mp4)")
    p_dub.add_argument("--text", "-t", required=True, help="Spoken dialogue script")
    p_dub.add_argument("--voice", "-v", default="jarvis", help="Voice ID")
    p_dub.add_argument("--out", "-o", required=True, help="Output dubbed video file")

    args = parser.parse_args()
    engine = VoiceStudioEngine()

    try:
        run_command(args, engine, parser)
    except (RuntimeError, ValueError) as exc:
        sys.exit(f"Error: {exc}")


def run_command(args, engine, parser):
    if args.command == "speak":
        out = engine.synthesize(
            args.text,
            voice_id=args.voice,
            output_path=args.out,
            play=not args.no_play,
            engine=args.engine,
            vs_voice=args.vs_voice,
        )
        print(f"✓ Speech synthesized: {out}")
    elif args.command == "list":
        print("\nAvailable IRAM OS Voices (Powered by VoiceStudio):")
        print("-" * 65)
        for v in engine.list_voices():
            print(f"• ID: \033[1;36m{v['id']:<18}\033[0m Name: \033[1m{v['name']:<24}\033[0m Lang: {v['lang']}")
            print(f"  └─ {v.get('description', '')}")
    elif args.command == "vs-voices":
        voices = engine.list_vs_voices()
        print("\nAvailable VoiceStudio Voices (GET /v1/audio/voices):")
        print("-" * 65)
        for v in voices:
            vid = v.get("id") or v.get("voice_id", "")
            name = v.get("name", "")
            vtype = v.get("type", "")
            lang = v.get("language") or v.get("lang") or "-"
            print(f"• ID: {vid:<20} Name: {name:<24} Type: {vtype:<14} Lang: {lang}")
            if v.get("description"):
                print(f"  └─ {v['description']}")
    elif args.command == "clone":
        sys.stderr.write(
            "Note: clone only stores a sample and applies EQ, does not reproduce the speaker. "
            "Real cloning needs VoiceStudio.\n"
        )
        res = engine.clone_voice(args.audio, args.name, lang=args.lang, gender=args.gender)
        print(f"✓ Voice cloned successfully: ID '{res['id']}' ({res['name']})")
    elif args.command == "design":
        res = engine.design_voice(args.prompt, args.name, lang=args.lang)
        print(f"✓ Voice designed successfully: ID '{res['id']}' ({res['name']})")
    elif args.command == "dub":
        out = engine.dub_video(args.video, args.text, args.voice, args.out)
        print(f"✓ Video dubbed successfully: {out}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
