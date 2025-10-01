import json
from typing import Dict, List, Optional

from llm_client import get_client, has_online_llm


SCHEMA_HINT = {
    "agent_id": "string",
    "title": "string",
    "synopsis": "string",
    "characters": ["string"],
    "relationships": ["string"],
    "main_plot_points": ["string"],
    "alternate_possibilities": ["string"],
    "possible_plotholes": ["string"],
    "themes": ["string"],
    "timeline_events": ["string"],
    "tags": ["string"],
}


def build_summary_prompt(chapter_text: str) -> List[Dict[str, str]]:
    system = {
        "role": "system",
        "content": (
            "You are a precise story analyst. Return only valid JSON with the fields: "
            f"{list(SCHEMA_HINT.keys())}. Values should be concise and factual."
        ),
    }
    user = {
        "role": "user",
        "content": (
            "Summarize the following chapter into the required JSON schema.\n\n"
            f"Chapter:\n{chapter_text}\n\n"
            f"Schema example (types only):\n{json.dumps(SCHEMA_HINT)}"
        ),
    }
    return [system, user]


def summarize_chapter(chapter_text: str, title_hint: Optional[str] = None) -> Dict:
    """Generate structured metadata for a chapter text.

    Falls back to a simple local heuristic if online LLM is unavailable.
    """
    if not chapter_text.strip():
        return {
            "agent_id": "",
            "title": title_hint or "Untitled",
            "synopsis": "",
            "characters": [],
            "relationships": [],
            "main_plot_points": [],
            "alternate_possibilities": [],
            "possible_plotholes": [],
            "themes": [],
            "timeline_events": [],
            "tags": [],
        }

    if has_online_llm():
        client = get_client()
        messages = build_summary_prompt(chapter_text)
        raw = client.chat(messages, temperature=0.2, max_tokens=800, response_format={"type": "json_object"})
        try:
            data = json.loads(raw)
        except Exception:
            # Attempt to extract JSON
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(raw[start : end + 1])
                except Exception:
                    data = {}
            else:
                data = {}
    else:
        # Offline heuristic: simple first-sentence synopsis and naive tags
        first_sentence = chapter_text.split(".")[0].strip()
        data = {
            "agent_id": "",
            "title": title_hint or first_sentence[:60] or "Untitled",
            "synopsis": first_sentence,
            "characters": [],
            "relationships": [],
            "main_plot_points": [],
            "alternate_possibilities": [],
            "possible_plotholes": [],
            "themes": [],
            "timeline_events": [],
            "tags": ["offline-summary"],
        }

    # Normalize and fill required keys
    for key, default in SCHEMA_HINT.items():
        if key not in data:
            data[key] = [] if isinstance(default, list) else ""
    if title_hint and not data.get("title"):
        data["title"] = title_hint
    return data


