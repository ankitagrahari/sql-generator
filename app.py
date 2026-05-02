"""
SQL Generator — AI-Powered SQL from Plain English
==================================================
Author:       backendbrilliance
Organization: EPAM
Website:      https://dynamicallyblunttech.com
Version:      1.0
"""

import os
import re
import uuid
import yaml
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")

BASE_DIR   = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


# ─── Schema helpers ────────────────────────────────────────────────────────────

def parse_yaml_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "tables" not in data:
        raise ValueError("Invalid ERD: missing top-level 'tables' key")
    return data["tables"]


def schema_to_prompt(schema: dict) -> str:
    lines = []
    for tname, tinfo in schema.items():
        cols   = tinfo.get("columns", {})
        pk     = []
        fk_cmt = []
        for c in tinfo.get("constraints", {}).values():
            ct = c.get("type", "")
            if ct == "PRIMARY KEY":
                pk = c.get("columnNames", [])
            elif ct == "FOREIGN KEY":
                fc  = ", ".join(c.get("columnNames", []))
                tt  = c.get("targetTableName", "")
                tc  = ", ".join(c.get("targetColumnNames", []))
                fk_cmt.append(f"  -- FK {fc} → {tt}({tc})")
        lines.append(f"TABLE {tname} (")
        for cname, cinfo in cols.items():
            nn  = " NOT NULL" if cinfo.get("notNull") else ""
            df  = f" DEFAULT {cinfo['default']}" if "default" in cinfo else ""
            lines.append(f"  {cname} {cinfo.get('type','?')}{nn}{df}")
        if pk:
            lines.append(f"  PRIMARY KEY ({', '.join(pk)})")
        lines.extend(fk_cmt)
        lines.append(")\n")
    return "\n".join(lines)


def schema_to_api(schema: dict) -> list:
    tables = []
    for tname, tinfo in schema.items():
        pks, fks = set(), {}
        for c in tinfo.get("constraints", {}).values():
            ct = c.get("type", "")
            if ct == "PRIMARY KEY":
                pks.update(c.get("columnNames", []))
            elif ct == "FOREIGN KEY":
                for col in c.get("columnNames", []):
                    fks[col] = {
                        "targetTable":   c.get("targetTableName"),
                        "targetColumns": c.get("targetColumnNames", []),
                    }
        columns = [
            {
                "name":         cname,
                "type":         cinfo.get("type", "?"),
                "notNull":      cinfo.get("notNull", False),
                "isPrimaryKey": cname in pks,
                "isForeignKey": cname in fks,
                "foreignKey":   fks.get(cname),
            }
            for cname, cinfo in tinfo.get("columns", {}).items()
        ]
        tables.append({"name": tname, "columns": columns, "columnCount": len(columns)})
    tables.sort(key=lambda x: x["name"])
    return tables


def active_schema() -> tuple:
    """Return (schema_dict, prompt_str, erd_name, is_custom) for current session.
    Returns (None, None, None, False) when no ERD has been uploaded."""
    erd_id   = session.get("erd_id")
    erd_name = session.get("erd_name", "")
    if erd_id:
        p = UPLOAD_DIR / f"{erd_id}.yaml"
        if p.exists():
            try:
                s = parse_yaml_file(p)
                return s, schema_to_prompt(s), erd_name, True
            except Exception:
                pass
    return None, None, None, False


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/schema")
def get_schema():
    schema, _, erd_name, is_custom = active_schema()
    if schema is None:
        return jsonify({"tables": [], "total": 0, "erd_name": None, "is_custom": False})
    return jsonify({
        "tables":    schema_to_api(schema),
        "total":     len(schema),
        "erd_name":  erd_name,
        "is_custom": True,
    })


@app.route("/api/upload-erd", methods=["POST"])
def upload_erd():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected"}), 400
    if not re.search(r"\.(yaml|yml)$", f.filename, re.I):
        return jsonify({"error": "Only .yaml / .yml files are accepted"}), 400

    raw = f.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        return jsonify({"error": "File exceeds 5 MB limit"}), 400

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return jsonify({"error": f"Invalid YAML: {e}"}), 400

    if not isinstance(data, dict) or "tables" not in data:
        return jsonify({"error": "ERD must have a top-level 'tables' key"}), 400
    if not data["tables"]:
        return jsonify({"error": "ERD contains no tables"}), 400

    erd_id = str(uuid.uuid4())
    (UPLOAD_DIR / f"{erd_id}.yaml").write_bytes(raw)

    session["erd_id"]   = erd_id
    session["erd_name"] = f.filename

    api_tables = schema_to_api(data["tables"])
    return jsonify({
        "success":   True,
        "erd_name":  f.filename,
        "tables":    api_tables,
        "total":     len(api_tables),
        "is_custom": True,
    })


@app.route("/api/reset-erd", methods=["POST"])
def reset_erd():
    session.pop("erd_id",   None)
    session.pop("erd_name", None)
    return jsonify({"tables": [], "total": 0, "erd_name": None, "is_custom": False})


# ─── SQL Generation ────────────────────────────────────────────────────────────

PROVIDERS = {
    "openai": {"base_url": None,                                    "needs_key": True},
    "github": {"base_url": "https://models.inference.ai.azure.com", "needs_key": True},
    "ollama": {"base_url": "http://host.docker.internal:port:11434/",               "needs_key": False},
}


@app.route("/api/generate", methods=["POST"])
def generate_sql():
    body     = request.get_json(force=True)
    prompt   = (body.get("prompt")   or "").strip()
    provider = (body.get("provider") or "openai").lower()
    model    = (body.get("model")    or "gpt-4o-mini").strip()
    api_key  = (body.get("api_key")  or "").strip()
    base_url = (body.get("base_url") or "").strip() or None

    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    pconf            = PROVIDERS.get(provider, PROVIDERS["openai"])
    resolved_baseurl = base_url or pconf["base_url"]

    if not api_key:
        api_key = {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "github": os.getenv("GITHUB_TOKEN", ""),
            "ollama": "ollama",
        }.get(provider, "")

    if pconf["needs_key"] and not api_key:
        label = {"openai": "OpenAI API key", "github": "GitHub Personal Access Token"}.get(provider, "API key")
        return jsonify({"error": f"{label} is missing. Click 'LLM Provider' to configure it."}), 400

    _, schema_summary, erd_name, _ = active_schema()

    if schema_summary is None:
        return jsonify({"error": "No ERD uploaded. Please upload a YAML ERD file first."}), 400

    system_prompt = f"""You are an expert SQL developer specialising in PostgreSQL.
You are given a complete database schema (ERD) and must translate the user's natural language \
request into an accurate, well-formatted SQL query.

DATABASE SCHEMA ({erd_name}):
{schema_summary}

RULES:
1. Write valid PostgreSQL SQL.
2. Use short, meaningful table aliases.
3. Add brief inline comments for non-obvious JOINs or WHERE conditions.
4. Use UPPERCASE SQL keywords, indent with 4 spaces.
5. Return ONLY the raw SQL — no markdown fences, no explanations.
6. Make sensible assumptions for ambiguous requests.
7. Prefer CTEs (WITH …) for complex multi-step queries.
8. Add ORDER BY for any query that returns a list."""

    try:
        kwargs = {"api_key": api_key}
        if resolved_baseurl:
            kwargs["base_url"] = resolved_baseurl

        print(f"--- API Request Log ---")
        print(f"Provider Requested: {provider}")
        print(f"Resolved Base URL Used: {resolved_baseurl}")
        print(f"Prompt: {prompt[:50]}...")
        print(f"-----------------------")
        resp = OpenAI(**kwargs).chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )

        sql = resp.choices[0].message.content.strip()
        sql = re.sub(r"^```[a-z]*\n?", "", sql, flags=re.I)
        sql = re.sub(r"\n?```$",        "", sql)

        u = resp.usage
        return jsonify({
            "sql":               sql.strip(),
            "model":             model,
            "provider":          provider,
            "prompt_tokens":     u.prompt_tokens     if u else 0,
            "completion_tokens": u.completion_tokens if u else 0,
        })

    except Exception as exc:
        msg = str(exc)
        if any(k in msg.lower() for k in ("api_key", "authentication", "401")):
            msg = {
                "github": "Invalid GitHub PAT — check token permissions.",
                "ollama": "Cannot reach Ollama — is it running?",
            }.get(provider, "Invalid API key — check your OpenAI key in settings.")
        elif "quota" in msg.lower() or "429" in msg:
            msg = "Rate limit / quota exceeded — check your billing."
        elif any(k in msg.lower() for k in ("connection", "refused", "connect")):
            msg = "Connection refused. Make sure Ollama is running on the configured URL."
        return jsonify({"error": msg}), 500


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print("🚀  SQL Generator  →  http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=debug)
