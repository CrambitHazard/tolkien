from typing import List

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

from fs_io import ensure_directories, get_next_chapter_index, get_latest_choices_index, read_last_n_canonical_metadata, read_last_n_pruned_metadata, write_choice_drafts
from generator import generate_three_options
from finalizer import finalize_selection


app = Flask(__name__)


INDEX_HTML = """
<!doctype html>
<title>3-Choice Chapter Writer</title>
<h1>3-Choice Chapter Writer</h1>
<form method="post" action="{{ url_for('generate') }}">
  <label>Context chapters (N): <input type="number" name="n" value="5" min="0" /></label>
  <button type="submit">Generate Options</button>
</form>
{% if chapter_index %}
  <h2>Options for Chapter {{ '%04d' % chapter_index }}</h2>
  <form method="post" action="{{ url_for('choose') }}">
    <label>Choose: 
      <select name="option">
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="C">C</option>
      </select>
    </label>
    <label>Context N: <input type="number" name="n" value="5" min="0" /></label>
    <button type="submit">Finalize</button>
  </form>
{% endif %}
"""


@app.get("/")
def index():
    return render_template_string(INDEX_HTML, chapter_index=None)


@app.post("/generate")
def generate():
    ensure_directories()
    n = int(request.form.get("n", 5))
    canon_ctx = read_last_n_canonical_metadata(1)
    pruned_ctx = read_last_n_pruned_metadata(n)
    drafts = generate_three_options(canon_ctx, pruned_ctx)
    chapter_index = get_next_chapter_index()
    write_choice_drafts(chapter_index, drafts)
    return render_template_string(INDEX_HTML, chapter_index=chapter_index)


@app.post("/choose")
def choose():
    option = request.form.get("option", "A").upper()
    n = int(request.form.get("n", 5))
    chapter_index = get_latest_choices_index()
    if chapter_index < 1:
        return jsonify({"error": "No drafts to choose."}), 400

    # Rebuild drafts from saved files
    drafts: List[dict] = []
    base = f"chapters/choices/{chapter_index:04d}"
    for label in ["A", "B", "C"]:
        try:
            import frontmatter
            with open(f"{base}/{label}.md", "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
            drafts.append({"id": label, "title": post.get("title", f"Option {label}"), "content": post.content})
        except FileNotFoundError:
            continue
    canon_ctx = read_last_n_canonical_metadata(1)
    finalize_selection(
        chapter_index=chapter_index,
        selected_option_id=option,
        drafts=drafts,
        context_metadata=canon_ctx,
    )
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)


