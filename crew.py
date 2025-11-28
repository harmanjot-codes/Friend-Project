# crew.py
import os
import json
import re
from typing import Dict, Any, Optional

# Try import Google Gemini SDK. If not installed, we will raise an error later.
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except Exception:
    GEMINI_SDK_AVAILABLE = False

# Look for API key: first prefer GEMINI_API_KEY, else fallback to SESSION_SECRET (your current secret name)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("SESSION_SECRET")

if not GEMINI_API_KEY:
    # we don't raise here — let the class handle missing key so the app can still run with fallback logic
    print("⚠️  No Gemini API key found in GEMINI_API_KEY or SESSION_SECRET. Model calls will fail.")

if GEMINI_SDK_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("🔑 Gemini configured.")
    except Exception as e:
        print("⚠️ Failed to configure Gemini:", e)
else:
    if not GEMINI_SDK_AVAILABLE:
        print("⚠️ google.generativeai SDK not available. Install it if you want real model calls.")
    else:
        print("⚠️ Gemini SDK available but API key missing.")

class HouseCrew:
    """
    HouseCrew generates a house construction plan using Gemini (if configured)
    Fall back to a locally generated basic plan if model calls fail.
    """

    def __init__(self):
        self.available = GEMINI_SDK_AVAILABLE and bool(GEMINI_API_KEY)

    def _clean_json_from_text(self, text: str) -> Optional[str]:
        """
        Extract json content from possible fenced response:
        - look for ```json ... ``` or first {...}
        """
        text = text.strip()
        # If triple fenced JSON, extract content
        if "```" in text:
            parts = text.split("```")
            # find the fenced part that contains a brace
            for p in parts:
                if "{" in p:
                    candidate = p
                    # remove "json" if present
                    candidate = candidate.replace("json", "", 1).strip()
                    # try to find first { ... } substring
                    m = re.search(r"(\{.*\})", candidate, flags=re.S)
                    if m:
                        return m.group(1)
                    return candidate.strip()
        # otherwise find the first {...} block
        m = re.search(r"(\{.*\})", text, flags=re.S)
        if m:
            return m.group(1)
        # maybe it's plain JSON array/object
        return None

    def _local_fallback_plan(self, area, budget, rooms, style, furniture) -> Dict[str, Any]:
        # Simple local fallback to ensure app always returns something
        rooms_int = None
        try:
            rooms_int = int(rooms)
        except Exception:
            rooms_int = None

        room_plan = []
        if rooms_int and rooms_int > 0:
            base = max(8, int(int(area) // max(1, rooms_int)))
            for i in range(1, rooms_int + 1):
                room_plan.append({"room": f"Room {i}", "size": f"{base}x{base} ft"})
        else:
            room_plan = [
                {"room": "Master Bedroom", "size": "12x14 ft"},
                {"room": "Living Room", "size": "14x16 ft"},
                {"room": "Kitchen", "size": "10x12 ft"}
            ]

        return {
            "summary": f"Local fallback plan: {rooms} rooms, style={style}, furniture={furniture}",
            "room_plan": room_plan,
            "materials": ["Cement - 30 bags", "Bricks - 5000 units", "Sand - 10 tons"],
            "estimated_cost": f"₹{budget} (approx)",
            "design_features": ["Natural ventilation", "Basic modern lighting"]
        }

    def generate_plan(self, area: str, budget: str, rooms: str, style: str, furniture: str) -> Dict[str, Any]:
        """
        Try to generate plan via Gemini if available, else return local fallback plan.
        """
        if not self.available:
            print("ℹ️ Gemini not available - using local fallback plan.")
            return self._local_fallback_plan(area, budget, rooms, style, furniture)

        # models to try (keeps trying if a model fails)
        models_to_try = ["gemini-pro", "gemini-1.5-flash", "gemini-2.0-flash", "text-bison-001"]

        prompt = f"""
You are an expert architect AI. Create a HOUSE CONSTRUCTION PLAN with details.
Return EXACTLY a single valid JSON object (no extra text). Keys:
summary, room_plan (array of {{room, size}}), materials (array), estimated_cost, design_features (array).

Input:
- Area: {area} sq ft
- Budget: ₹{budget}
- Rooms: {rooms}
- Style: {style}
- Furniture included: {furniture}
"""

        last_err = None
        for model_name in models_to_try:
            try:
                print(f"🔄 Trying Gemini model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                # many SDK versions expose response.text or response.output[0].content
                text = getattr(response, "text", None) or getattr(response, "content", None)
                if not text and hasattr(response, "candidates"):
                    # older responses might have candidates
                    text = response.candidates[0].output[0].content if response.candidates else None
                if not text:
                    text = str(response)
                text = text.strip()
                print("🔎 raw response (start):", text[:200])

                cleaned = self._clean_json_from_text(text)
                if not cleaned:
                    # maybe the model returned a pure JSON array/object
                    cleaned = text

                # Try parse
                plan = json.loads(cleaned)
                print(f"✅ Parsed plan from {model_name}")
                return plan

            except Exception as e:
                last_err = e
                print(f"❌ Model {model_name} failed: {e}")
                continue

        print("⚠️ All Gemini models failed, returning local fallback. Last error:", last_err)
        return self._local_fallback_plan(area, budget, rooms, style, furniture)
