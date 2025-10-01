from typing import Dict, List, Tuple

from llm_client import get_client, has_online_llm


GENERATOR_SYSTEM = (
    "You are an expert fantasy novelist. Generate three distinct full chapter drafts "
    "that are STRICT continuations of the most recent canonical chapter only. Do not "
    "continue non-canonical or pruned branches. Each option must follow different "
    "narrative directions (unique conflicts, settings, or outcomes) while remaining "
    "compatible with the canonical facts. Avoid contradictions."
)


def build_generation_prompt(
    canonical_context: List[Tuple[str, dict]],
    pruned_context: List[Tuple[str, dict]],
) -> List[dict]:
    system = {"role": "system", "content": GENERATOR_SYSTEM}
    synopsis_lines: List[str] = []
    for filename, meta in canonical_context:
        title = meta.get("title", filename)
        synopsis = meta.get("synopsis", "")
        facts = ", ".join(meta.get("main_plot_points", [])[:5])
        synopsis_lines.append(f"- CANON {title}: {synopsis} | Facts: {facts}")

    dream_lines: List[str] = []
    for filename, meta in pruned_context:
        title = meta.get("title", filename)
        synopsis = meta.get("synopsis", "")
        hints = ", ".join(meta.get("themes", [])[:3])
        dream_lines.append(f"- PRUNED {title}: {synopsis} | Themes: {hints}")
    user = {
        "role": "user",
        "content": (
            "Continuity context (canonical metadata only, latest last):\n" + "\n".join(synopsis_lines) +
            ("\n\nPruned timelines (use only as dreams/omens/echoes):\n" + "\n".join(dream_lines) if dream_lines else "") +
            "\n\nInstructions:\n"
            "- Produce THREE drafts labeled A, B, C.\n"
            "- Each draft must be at least 900 words.\n"
            "- Keep styles consistent with a single authorial voice.\n"
            "- Ensure each option has unique narrative beats and tone.\n"
            "- Each option must begin where the last canonical chapter leaves off.\n"
            "- Pruned context may only appear as dreams, visions, prophecies, deja-vu, or literary echoes.\n"
            "- Do not import pruned facts as real events in the canonical.\n"
            "- Do not include analysis or comments. Return plain prose with labels.\n\n"
            "Output format:\n"
            "Option A:\n<full text>\n\nOption B:\n<full text>\n\nOption C:\n<full text>\n"
        ),
    }
    return [system, user]


def parse_three_options(text: str) -> List[Dict[str, str]]:
    chunks = []
    current_label = None
    buffer: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("option a"):
            if current_label and buffer:
                chunks.append({"id": current_label, "title": f"Option {current_label}", "content": "\n".join(buffer).strip()})
            current_label = "A"
            buffer = []
            continue
        if stripped.lower().startswith("option b"):
            if current_label and buffer:
                chunks.append({"id": current_label, "title": f"Option {current_label}", "content": "\n".join(buffer).strip()})
            current_label = "B"
            buffer = []
            continue
        if stripped.lower().startswith("option c"):
            if current_label and buffer:
                chunks.append({"id": current_label, "title": f"Option {current_label}", "content": "\n".join(buffer).strip()})
            current_label = "C"
            buffer = []
            continue
        buffer.append(line)
    if current_label and buffer:
        chunks.append({"id": current_label, "title": f"Option {current_label}", "content": "\n".join(buffer).strip()})

    found_ids = {c["id"] for c in chunks}
    # Ensure three outputs by padding minimal placeholders if parsing is brittle
    for label in ["A", "B", "C"]:
        if label not in found_ids:
            chunks.append({"id": label, "title": f"Option {label}", "content": "[Missing content]"})
    # Keep stable order A, B, C
    chunks_sorted = sorted(chunks, key=lambda d: d["id"])[:3]
    return chunks_sorted


def generate_three_options(
    canonical_context: List[Tuple[str, dict]],
    pruned_context: List[Tuple[str, dict]],
) -> List[Dict[str, str]]:
    if has_online_llm():
        client = get_client()
        messages = build_generation_prompt(canonical_context, pruned_context)
        raw = client.chat(messages, temperature=1.05, max_tokens=6000)
        return parse_three_options(raw)
    else:
        # Offline stub drafts
        stub = (
            "This is an offline stub draft. Replace with real content when the LLM is available."
        )
        return [
            {"id": "A", "title": "Option A", "content": stub},
            {"id": "B", "title": "Option B", "content": stub},
            {"id": "C", "title": "Option C", "content": stub},
        ]


