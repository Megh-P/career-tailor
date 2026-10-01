"""Run one ATS tailoring job: validate template -> agent (job intake + Technical Skills rewrite) -> ats check -> render
-> copy the PDF to the output dir.

  python tailor.py --template <path.md> --jd-file <path> --work-dir <dir> --out-dir <dir> [--skills <skills.md>]
                   [--agent claude] [--model sonnet] [--id <id>] [--name-format "{name} Resume - {company} {role}"]

Prints the run record as JSON on the last stdout line and writes it to <work-dir>/<date>-<company>-<role>/run.json.
Exit 1 on failure (the record has "error"). The pasted job description is untrusted data for the agent.
"""
import argparse, datetime, json, os, pathlib, re, shutil, subprocess, sys, uuid

BACKEND = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))
from resume import validate_file, read, skills_from_template, parse_skills, sync  # noqa: E402

DEFAULT_NAME_FORMAT = "{name} Resume - {company} {role}"
AGENTS = ("claude",)  # codex CLI / direct API are roadmap items; add a branch in run_agent()

SCHEMA = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean", "description": "ats check printed ok and render printed pages: 1"},
        "company": {"type": "string"},
        "role": {"type": "string"},
        "pdf": {"type": "string", "description": "absolute path of the rendered PDF in the job directory"},
        "skills_added": {"type": "array", "items": {"type": "string"}},
        "new_adjacent": {"type": "array", "items": {"type": "string"}},
        "gaps": {"type": "array", "items": {"type": "string"}},
        "error": {"type": "string", "description": "empty unless ok is false"},
    },
    "required": ["ok", "company", "role", "pdf", "skills_added", "new_adjacent", "gaps", "error"],
}


def clean(s):
    """Filename-safe: strip reserved characters, collapse whitespace, trim trailing dots/spaces, cap length."""
    s = re.sub(r"\s+", " ", re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", s)).strip(" .")
    return s[:80].strip(" .") or "Unknown"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "unknown"


def out_name(fmt, name, company, role):
    try:
        text = fmt.format(name=name, company=company, role=role)
    except (KeyError, IndexError, ValueError):
        text = DEFAULT_NAME_FORMAT.format(name=name, company=company, role=role)
    return clean(re.sub(r"\s+", " ", text))[:150] + ".pdf"


def run_agent(agent, model, prompt, cwd, add_dirs, log):
    if agent != "claude":
        raise ValueError(f"--agent {agent!r} is not supported yet; only 'claude' is implemented")
    cmd = [shutil.which("claude") or "claude", "-p", prompt, "--model", model, "--output-format", "json",
           "--json-schema", json.dumps(SCHEMA), "--permission-mode", "acceptEdits",
           "--allowedTools", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "Bash(python:*)",
           "Bash(PYTHONIOENCODING=utf-8 python:*)", "Bash(mkdir:*)", "Bash(ls:*)", "Bash(cp:*)"]
    for d in add_dirs:
        cmd += ["--add-dir", str(d)]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=900, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log.write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
    out = json.loads(r.stdout)
    return out.get("structured_output") or json.loads(out.get("result") or "{}")


def run(a):
    today = datetime.date.today().isoformat()
    work = pathlib.Path(a.work_dir).resolve()
    rec = {"id": a.id, "template": str(a.template), "template_snapshot": "", "status": "failed", "company": "", "role": "",
           "folder": "", "pdf": "", "output": "", "skills_added": [], "new_adjacent": [], "gaps": [], "error": "",
           "started": datetime.datetime.now().isoformat(timespec="seconds"), "finished": ""}
    job = work / f"{today}-{a.id}"
    try:
        job.mkdir(parents=True, exist_ok=True)
        rec["folder"] = str(job)
        if a.agent not in AGENTS:
            raise ValueError(f"--agent {a.agent!r} is not supported yet; only 'claude' is implemented")
        template = pathlib.Path(a.template).resolve()
        if template.with_suffix(".txt").is_file():  # a .txt twin you edited by hand wins if it's newer
            sync(template)
        v = validate_file(template)
        if not v["ok"]:
            raise ValueError(f"template {template.name} is invalid: " + "; ".join(v["errors"]))
        rec["template_snapshot"] = read(template)
        skills = pathlib.Path(a.skills).resolve() if a.skills else work / "skills.md"
        if not skills.is_file():
            skills.parent.mkdir(parents=True, exist_ok=True)
            skills.write_text(skills_from_template(rec["template_snapshot"]), encoding="utf-8")
        if not any(parse_skills(read(skills))):
            raise ValueError(f"skills file {skills} has no '- <Skill>' lines under '## Skills'")
        jd = job / "jd.txt"
        shutil.copyfile(a.jd_file, jd)
        prompt = (BACKEND / "prompts" / "tailor.md").read_text(encoding="utf-8").format(
            date=today, backend=BACKEND.as_posix(), template=template.as_posix(), skills=skills.as_posix(),
            job_dir=job.as_posix(), jd=jd.as_posix())
        res = run_agent(a.agent, a.model, prompt, job, [BACKEND, template.parent, skills.parent], job / "agent.log")
        rec.update({k: res.get(k, rec[k]) for k in ("company", "role", "skills_added", "new_adjacent", "gaps", "error")})
        if not res.get("ok"):
            raise RuntimeError(res.get("error") or "the agent reported failure")
        pdf = pathlib.Path(res["pdf"])
        pdf = pdf if pdf.is_absolute() else job / pdf
        if not pdf.is_file():
            raise FileNotFoundError(f"agent did not produce the PDF: {pdf}")
        dest_dir = pathlib.Path(a.out_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / out_name(a.name_format, clean(v["name"]), clean(res["company"]), clean(res["role"]))
        shutil.copyfile(pdf, dest)
        rec.update(status="done", output=str(dest), pdf=str(pdf), error="")
        # rename the job dir to <date>-<company>-<role> now that the agent has named them
        final = work / f"{today}-{slug(res['company'])}-{slug(res['role'])}"
        if final != job and not final.exists():
            job.rename(final)
            rec.update(folder=str(final), pdf=str(final / pdf.name))
            job = final
    except Exception as ex:  # validation, timeout, bad JSON, missing PDF; agent output is in <job>/agent.log
        rec.update(status="failed", error=f"{type(ex).__name__}: {ex}"[:1500] if not isinstance(ex, ValueError) else str(ex)[:1500])
    rec["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    if job.is_dir():
        (job / "run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", required=True)
    ap.add_argument("--jd-file", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--skills")
    ap.add_argument("--agent", default="claude")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--id", default=None)
    ap.add_argument("--name-format", default=DEFAULT_NAME_FORMAT)
    a = ap.parse_args(argv)
    a.id = clean(a.id or uuid.uuid4().hex[:8]).replace(" ", "-")
    rec = run(a)
    print(json.dumps(rec, ensure_ascii=False))
    return 0 if rec["status"] == "done" else 1


def selftest():
    assert clean('a<b>:c"/d\\e|f?g*  h. ') == "abcdefg h"
    assert out_name("{name} Resume - {company} {role}", "Alex Rivera", "Acme", "SWE") == "Alex Rivera Resume - Acme SWE.pdf"
    assert out_name("{bogus}", "A", "B", "C") == "A Resume - B C.pdf"
    assert slug("Acme, Inc.") == "acme-inc"
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        selftest()
    else:
        sys.exit(main(sys.argv[1:]))
