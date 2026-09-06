import json
import logging
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini Generative AI API with automatic fallback resilience."""

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if a live GEMINI_API_KEY is configured."""
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() and "mock" not in settings.GEMINI_API_KEY.lower())

    @classmethod
    def generate_text(cls, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Synchronously generate text using Gemini API if configured.
        Returns the raw string output, or None if offline/unconfigured.
        """
        if not cls.is_configured():
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        
        contents = []
        if system_instruction:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System Context:\n{system_instruction}\n\nTask:\n{prompt}"}]
            })
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 2048,
            }
        }

        # Multi-model resilience: try configured model, then fast fallbacks on 503/404
        models_to_try = [settings.GEMINI_MODEL, "gemini-flash-latest", "gemini-3.6-flash"]
        seen = set()
        deduped_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

        for model_name in deduped_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
            
            # Prepare payload: disable thinking delay on flash-latest for instant 1.5s latency
            req_payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.2,
                    "topP": 0.8,
                    "maxOutputTokens": 2048,
                }
            }
            if "flash-latest" in model_name:
                req_payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}

            try:
                timeout_sec = 15.0 if "flash-latest" in model_name else 35.0
                with httpx.Client(timeout=timeout_sec) as client:
                    response = client.post(url, json=req_payload)
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    elif response.status_code in (503, 404):
                        logger.info(f"Model {model_name} returned status {response.status_code}, trying fallback model...")
                        continue
                    elif response.status_code == 400 and "thinkingConfig" in req_payload["generationConfig"]:
                        # Retry once without thinkingConfig if rejected
                        req_payload["generationConfig"].pop("thinkingConfig", None)
                        retry_resp = client.post(url, json=req_payload)
                        if retry_resp.status_code == 200:
                            candidates = retry_resp.json().get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    return parts[0].get("text", "")
                    else:
                        logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
                        continue
            except Exception as e:
                logger.warning(f"Gemini invocation for {model_name} failed ({e}), trying fallback...")
                continue

        return None

