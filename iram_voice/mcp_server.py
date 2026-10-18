#!/usr/bin/env python3
"""
IRAM OS VoiceStudio MCP Server
Exposes voice cloning, synthesis, and audio tools to AI Agents (Antigravity CLI, OpenClaw, Gemini).
Complies with Model Context Protocol (MCP) spec over JSON-RPC stdio.
"""

import sys
import json
import logging
from typing import Dict, Any

from iram_voice.core import VoiceStudioEngine

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("iram_voice.mcp")


class VoiceStudioMCPServer:
    def __init__(self):
        self.engine = VoiceStudioEngine()

    def handle_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        msg_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "iram-voicestudio-mcp",
                        "version": "1.0.0"
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "generate_speech",
                            "description": "Synthesizes spoken audio from text using VoiceStudio neural voices or cloned profiles.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "description": "The text content to speak."},
                                    "voice_id": {"type": "string", "description": "Voice profile ID (e.g. 'jarvis', 'samantha', 'cinema-narrator', 'tamil-tech').", "default": "jarvis"},
                                    "play": {"type": "boolean", "description": "Play audio immediately through PipeWire speakers.", "default": True}
                                },
                                "required": ["text"]
                            }
                        },
                        {
                            "name": "clone_voice",
                            "description": "Enrolls a new voice profile from a reference audio file (.wav, .mp3).",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "audio_path": {"type": "string", "description": "Absolute path to reference audio file."},
                                    "voice_name": {"type": "string", "description": "Human-readable name for the new voice profile."},
                                    "lang": {"type": "string", "description": "Language code (e.g. 'en-US', 'ta-IN').", "default": "en-US"}
                                },
                                "required": ["audio_path", "voice_name"]
                            }
                        },
                        {
                            "name": "design_voice",
                            "description": "Designs a new synthetic persona using descriptive adjectives (e.g. 'deep authoritative narrator').",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "prompt": {"type": "string", "description": "Acoustic and character description."},
                                    "voice_name": {"type": "string", "description": "Name for the designed voice."}
                                },
                                "required": ["prompt", "voice_name"]
                            }
                        },
                        {
                            "name": "list_voices",
                            "description": "Lists all available pre-packaged and cloned voice profiles in VoiceStudio.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "check_health",
                            "description": "Returns VoiceStudio engine status, PipeWire availability, and active voices count.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            }

        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})

            try:
                if name == "generate_speech":
                    text = args.get("text", "")
                    voice_id = args.get("voice_id", "jarvis")
                    play = args.get("play", True)
                    out_path = self.engine.synthesize(text, voice_id=voice_id, play=play)
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Successfully generated speech audio at: {out_path} (Voice: {voice_id}, Played: {play})"
                                }
                            ]
                        }
                    }

                elif name == "clone_voice":
                    audio_path = args.get("audio_path")
                    voice_name = args.get("voice_name")
                    lang = args.get("lang", "en-US")
                    prof = self.engine.clone_voice(audio_path, voice_name, lang=lang)
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Voice successfully cloned. New Profile ID: '{prof['id']}'"
                                }
                            ]
                        }
                    }

                elif name == "design_voice":
                    prompt = args.get("prompt")
                    voice_name = args.get("voice_name")
                    prof = self.engine.design_voice(prompt, voice_name)
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Voice successfully designed. Profile ID: '{prof['id']}'"
                                }
                            ]
                        }
                    }

                elif name == "list_voices":
                    voices = self.engine.list_voices()
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(voices, indent=2)
                                }
                            ]
                        }
                    }

                elif name == "check_health":
                    voices = self.engine.list_voices()
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps({
                                        "status": "healthy",
                                        "engine": "VoiceStudio / OmniVoice",
                                        "voices_count": len(voices),
                                        "pipewire_playback": True
                                    }, indent=2)
                                }
                            ]
                        }
                    }

                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32601, "message": f"Method '{name}' not found"}
                    }

            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32000, "message": str(e)}
                }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Unknown method '{method}'"}
        }

    def run(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"Error handling message: {e}")


if __name__ == "__main__":
    server = VoiceStudioMCPServer()
    server.run()
