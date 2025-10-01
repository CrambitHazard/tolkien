from typing import Dict, List, Tuple

from fs_io import (
    write_canonical_chapter,
    write_pruned_chapter,
    write_metadata_json,
)
from summarizer import summarize_chapter
from llm_client import get_client, has_online_llm


def _build_tragic_prompt(draft_text: str, context_metadata: List[Tuple[str, dict]]) -> list:
    """Create messages to expand a branch into a complete tragic ending."""
    synopsis_lines: List[str] = []
    for _, meta in context_metadata:
        title = meta.get("title", "")
        synopsis = meta.get("synopsis", "")
        facts = ", ".join(meta.get("main_plot_points", [])[:6])
        synopsis_lines.append(f"- {title}: {synopsis} | Facts: {facts}")

    system = {
        "role": "system",
        "content": (
            "You are a skilled novelist. Your task is to take a draft chapter and "
            "complete the entire storyline of this branch with a tragic ending. The result "
            "must be a full, self-contained concluding chapter that provides closure for all "
            "active threads, consequences, and character arcs. Avoid contradictions with the "
            "continuity metadata. Output only narrative prose, no labels or commentary."
        ),
    }
    user = {
        "role": "user",
        "content": (
            "Continuity metadata (summaries only):\n" + "\n".join(synopsis_lines) +
            "\n\nDraft to expand into a complete tragic conclusion (keep voice & style):\n" +
            draft_text +
            "\n\nRequirements:\n"
            "- Conclude the storyline in this branch with a tragic ending.\n"
            "- Provide clear narrative closure (fates, consequences, thematic payoff).\n"
            "- 1200-2000 words.\n"
            "- No headings, no 'Option' labels, no YAML, no analysis.\n"
        ),
    }
    return [system, user]


def expand_to_tragic_ending(draft_text: str, context_metadata: List[Tuple[str, dict]]) -> str:
    """Use the LLM to produce a conclusive tragic ending for the branch.

    Falls back to a local minimal closure if offline.
    """
    if has_online_llm():
        client = get_client()
        messages = _build_tragic_prompt(draft_text, context_metadata)
        return client.chat(messages, temperature=0.9, max_tokens=6000)
    # Offline fallback: append a concise tragic closure
    return (
        draft_text.rstrip() +
        "\n\nIn the end, the choice unraveled every hope. Promises turned to ash, and what "
        "could have been a brighter path hardened into loss. The last light guttered, and "
        "the story closed on a silence that no prayer could lift."
    )


def finalize_selection(
    chapter_index: int,
    selected_option_id: str,
    drafts: List[Dict[str, str]],
    context_metadata: List[Tuple[str, dict]],
) -> Dict[str, str]:
    """Save canonical chapter and tragic branches, with metadata mirrors.

    Returns a dict of created file paths.
    """
    created: Dict[str, str] = {}
    # Prepare metadata context synopsis only (not used directly here, but could be embedded)
    # Save canonical
    selected = next((d for d in drafts if d["id"].upper() == selected_option_id.upper()), None)
    if selected is None:
        raise ValueError("Selected option not among drafts")

    canonical_meta = summarize_chapter(selected.get("content", ""), title_hint=selected.get("title"))
    canonical_path = write_canonical_chapter(
        chapter_index=chapter_index,
        title=canonical_meta.get("title", f"Chapter {chapter_index}"),
        content=selected.get("content", ""),
        metadata_yaml=canonical_meta,
    )
    created["canonical"] = canonical_path
    created["canonical_meta"] = write_metadata_json(
        filename=f"chapter-{chapter_index:04d}.json",
        data=canonical_meta,
    )

    # Save pruned branches
    for draft in drafts:
        option_id = draft.get("id", "").upper()
        if option_id == selected_option_id.upper():
            continue
        # Expand to a complete tragic ending for this branch
        tragic_text = expand_to_tragic_ending(draft.get("content", ""), context_metadata)
        tragic_meta = summarize_chapter(tragic_text, title_hint=draft.get("title"))
        path = write_pruned_chapter(
            chapter_index=chapter_index,
            option_id=option_id,
            title=tragic_meta.get("title", f"Chapter {chapter_index} - {option_id}"),
            content=tragic_text,
            metadata_yaml=tragic_meta,
        )
        created[f"pruned_{option_id}"] = path
        created[f"pruned_{option_id}_meta"] = write_metadata_json(
            filename=f"chapter-{chapter_index:04d}-{option_id}.json",
            data=tragic_meta,
        )

    return created


