import argparse
from typing import List

from fs_io import ensure_directories, get_next_chapter_index, get_latest_choices_index, list_history, read_last_n_canonical_metadata, read_last_n_pruned_metadata, write_choice_drafts
from generator import generate_three_options
from finalizer import finalize_selection


def cmd_generate(args: argparse.Namespace) -> None:
    ensure_directories()
    # Continuity must follow only the latest canonical chapter
    canon_ctx = read_last_n_canonical_metadata(1)
    pruned_ctx = read_last_n_pruned_metadata(args.n)
    drafts = generate_three_options(canon_ctx, pruned_ctx)
    chapter_index = get_next_chapter_index()
    paths = write_choice_drafts(chapter_index, drafts)
    print(f"Generated options for chapter {chapter_index:04d}:")
    for path in paths:
        print(f"  - {path}")


def cmd_choose(args: argparse.Namespace) -> None:
    option = args.option.upper()
    if option not in {"A", "B", "C"}:
        raise SystemExit("--option must be A, B, or C")

    # Load the latest choices directory explicitly
    chapter_index = get_latest_choices_index()
    if chapter_index < 1:
        raise SystemExit("No generated options to choose from.")

    # Collect drafts from files
    drafts: List[dict] = []
    base = f"chapters/choices/{chapter_index:04d}"
    for label in ["A", "B", "C"]:
        try:
            # Strip YAML frontmatter if present
            import frontmatter
            with open(f"{base}/{label}.md", "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
            drafts.append({"id": label, "title": post.get("title", f"Option {label}"), "content": post.content})
        except FileNotFoundError:
            continue
    if not drafts:
        raise SystemExit(f"No drafts found in {base}.")

    # Continue only from the latest canonical chapter
    canon_ctx = read_last_n_canonical_metadata(1)
    pruned_ctx = read_last_n_pruned_metadata(args.n)
    created = finalize_selection(
        chapter_index=chapter_index,
        selected_option_id=option,
        drafts=drafts,
        context_metadata=canon_ctx,  # finalizer uses canonical metadata for summaries/closure
    )
    print("Saved:")
    for k, v in created.items():
        print(f"  {k}: {v}")


def cmd_history(_: argparse.Namespace) -> None:
    hist = list_history()
    for key in ["canonical", "pruned", "choices"]:
        print(f"{key}:")
        for path in hist[key]:
            print(f"  - {path}")


def cmd_export(args: argparse.Namespace) -> None:
    mode = args.mode
    if mode not in {"canonical", "all"}:
        raise SystemExit("--mode must be 'canonical' or 'all'")
    # Simple export example: concatenate canonical chapters
    import os

    canonical_dir = "chapters/canonical"
    files = [
        name for name in sorted(os.listdir(canonical_dir)) if name.endswith(".md")
    ]
    output = []
    for name in files:
        with open(f"{canonical_dir}/{name}", "r", encoding="utf-8") as f:
            output.append(f.read())
    with open("canonical_export.md", "w", encoding="utf-8") as f:
        f.write("\n\n\n".join(output))
    print("Exported canonical chapters to canonical_export.md")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="3-Choice Chapter Writer Agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Generate three chapter options")
    g.add_argument("--n", type=int, default=5, help="Number of recent metadata items for context")
    g.set_defaults(func=cmd_generate)

    c = sub.add_parser("choose", help="Choose canonical option and finalize")
    c.add_argument("--option", type=str, required=True, help="A, B, or C")
    c.add_argument("--n", type=int, default=5, help="Number of recent metadata items for context")
    c.set_defaults(func=cmd_choose)

    h = sub.add_parser("history", help="Show filesystem history of chapters")
    h.set_defaults(func=cmd_history)

    e = sub.add_parser("export", help="Export storyline")
    e.add_argument("--mode", type=str, default="canonical")
    e.set_defaults(func=cmd_export)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


