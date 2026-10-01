"""Resume tools for the Career Tailor markdown dialect. Every command prints one JSON object on its last stdout line
(exit 0 ok, 1 failure).

  python resume.py validate <template.md> [--render]       # dialect + structure check; --render also checks 1 page
  python resume.py ats <template.md> <resume.md> --skills <skills.md>   # only Technical Skills may differ
  python resume.py sync <name[.md|.txt]>                   # fuse a .md/.txt pair: newer mtime is copied over the other
  python resume.py --test

Dialect: "# Name", contact lines, "## Section", "### Entry || Date", "- bullet" (only under an entry), other lines
are paragraphs. Skill lines (under "## Technical Skills") look like "**Label** – a, b, c". **bold**, *italic*.
Skills file: "## Skills" and "## Adjacent" sections of "- <Skill> · <note>" lines (note optional).
"""
import json, pathlib, re, shutil, sys

SLOP = ["leverag", "spearhead", "utiliz", "synerg", "cutting-edge", "seamless", "robust", "delve",
        "passionate", "dynamic", "innovative", "state-of-the-art", "world-class", "best-in-class",
        "empower", "orchestrat", "revolutioniz", "game-chang", "holistic", "streamlin", "fostering"]
SKILL = re.compile(r"^\*\*(.+?)(?::\*\*|\*\*\s*[–:-])\s*(.+)$")
SKILLS = "Technical Skills"


def parse(md):
    """-> {'head': [lines], 'sections': [(name, [block])]}; block = ('entry', text, [bullets]) | ('para', text)."""
    doc = {"head": [], "sections": []}
    for line in md.strip().splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("## "):
            doc["sections"].append((line[3:].strip(), []))
        elif not doc["sections"]:
            doc["head"].append(line)
        elif line.startswith("### "):
            doc["sections"][-1][1].append(("entry", line[4:], []))
        elif line.startswith("- "):
            blocks = doc["sections"][-1][1]
            if not blocks or blocks[-1][0] != "entry":
                raise ValueError(f"bullet outside an entry: {line[:60]}")
            blocks[-1][2].append(line[2:])
        else:
            doc["sections"][-1][1].append(("para", line))
    return doc


def plain(s):
    return re.sub(r"\*+", "", s)


def has_slop(s):
    s = s.lower()
    return [w for w in SLOP if re.search(r"\b" + w, s)]  # word-start match: "thermodynamically" is not "dynamic"


def read(p):
    return pathlib.Path(p).read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def emit(obj, ok=True):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(0 if ok else 1)


# ---------- validate ----------

def validate(text):
    """text -> result dict. Errors block a run; warnings do not."""
    errs, warns = [], []
    res = {"ok": False, "errors": errs, "warnings": warns, "name": "", "sections": [], "skill_labels": [], "skills": []}
    if not text.strip():
        errs.append("file is empty")
        return res
    lines = text.replace("\r\n", "\n").split("\n")
    first = next((i for i, l in enumerate(lines) if l.strip()), 0)
    if lines[first].startswith("# "):
        res["name"] = lines[first][2:].strip()
    else:
        errs.append(f"line {first + 1}: first line must be '# Your Name'")
    sec, entry, skills_sec = None, False, None
    for n, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if not line or n == first + 1:
            continue
        if line.startswith("## "):
            sec, entry = line[3:].strip(), False
            res["sections"].append(sec)
            if sec.lower() == SKILLS.lower():
                skills_sec = sec
                if sec != SKILLS:
                    warns.append(f"line {n}: section '{sec}' should be spelled '{SKILLS}'")
        elif sec is None:
            continue  # contact lines
        elif line.startswith("### "):
            entry = True
            if "||" not in line:
                warns.append(f"line {n}: entry has no '|| date' (expected '### Title || Dates')")
        elif sec.lower() == SKILLS.lower():
            m = SKILL.match(line)
            if m:
                items = [i.strip() for i in m.group(2).split(",") if i.strip()]
                res["skill_labels"].append(m.group(1))
                res["skills"] += items
            else:
                errs.append(f"line {n}: skill line must look like **Label** – a, b, c (got: {line[:50]!r})")
        elif line.startswith("- "):
            if not entry:
                errs.append(f"line {n}: bullet outside an entry; put a '### Title || Dates' line above it")
            for w in has_slop(line):
                warns.append(f"line {n}: filler word '{w}'")
    if not res["sections"]:
        errs.append("no '## ' sections found (e.g. '## Education', '## Technical Skills')")
    if not skills_sec:
        errs.append(f"no '## {SKILLS}' section; the tailor only edits that section, so it is required")
    elif not res["skill_labels"] and not any("skill line" in e for e in errs):
        errs.append(f"'## {SKILLS}' has no skill lines; add lines like **Languages** – Python, C++")
    flat = res["skills"]
    warns += [f"duplicate skill: {i}" for i in sorted({i for i in flat if flat.count(i) > 1})]
    if not errs:
        warns += [f"repeated opener: {w}" for w in repeated_openers(text)]
    res["ok"] = not errs
    return res


def validate_file(path):
    try:
        raw = pathlib.Path(path).read_bytes()
    except OSError as ex:
        return {"ok": False, "errors": [f"cannot read {path}: {ex.strerror or ex}"], "warnings": [], "name": "",
                "sections": [], "skill_labels": [], "skills": []}
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as ex:
        return {"ok": False, "errors": [f"file is not UTF-8 (byte {ex.start}); re-save it as UTF-8"], "warnings": [],
                "name": "", "sections": [], "skill_labels": [], "skills": []}
    return validate(text)


# ---------- skills file ----------

def parse_skills(text):
    """-> ({skill: note}, {skill: note}). '## Adjacent' lines are the adjacent tier; every other '## ' section counts as
    skills (so '## Languages' / '## Tools' layouts work), except sections whose title says 'domain', 'not listed' or
    'ignore', which are notes, not skills."""
    out, cur = {"skills": {}, "adjacent": {}}, None
    for line in text.replace("\r\n", "\n").splitlines():
        if line.startswith("## "):
            title = line[3:].strip().lower()
            cur = None if any(w in title for w in ("domain", "not listed", "ignore")) else \
                "adjacent" if title.startswith("adjacent") else "skills"
        elif line.startswith("- ") and cur:
            name, _, note = line[2:].partition(" · ")
            out[cur][name.strip()] = note.strip()
    return out["skills"], out["adjacent"]


def skills_from_template(template_md):
    """Seed text for a skills file: every skill in the template's skill lines."""
    items = []
    for lab, its in skill_lines(parse(template_md)).items():
        items += [i for i in its if i not in items]
    return "## Skills\n" + "".join(f"- {i}\n" for i in items) + "\n## Adjacent\n"


# ---------- ats ----------

def skill_lines(doc):
    """-> {label: [items]} for the Technical Skills section."""
    blocks = next((b for s, b in doc["sections"] if s.lower() == SKILLS.lower()), [])
    return {m.group(1): [i.strip() for i in m.group(2).split(",")] for b in blocks if b[0] == "para"
            for m in [SKILL.match(b[1])] if m}


def ats(template_md, new_md, allowed):
    """-> (errors, added, dropped, reorders). Everything but Technical Skills must equal the template."""
    t, n, errs = parse(template_md), parse(new_md), []
    if t["head"] != n["head"]:
        errs.append("header/contact lines changed")
    if [s.lower() for s, _ in t["sections"]] != [s.lower() for s, _ in n["sections"]]:
        return errs + ["sections added, removed, or reordered"], [], [], []
    for (sec, tb), (_, nb) in zip(t["sections"], n["sections"]):
        if sec.lower() != SKILLS.lower() and tb != nb:
            errs.append(f"{sec}: changed (only {SKILLS} may differ from the template)")
    ts, ns = skill_lines(t), skill_lines(n)
    if sorted(ts) != sorted(ns):
        errs.append(f"skill labels must stay {sorted(ts)}")
    flat = [i for items in ns.values() for i in items]
    errs += [f"duplicate skill: {i}" for i in sorted({i for i in flat if flat.count(i) > 1})]
    errs += [f"not in skills file: {i}" for i in flat if i not in allowed]
    old = [i for items in ts.values() for i in items]
    added, dropped = [i for i in flat if i not in old], [i for i in old if i not in flat]
    reorders = [{"label": lab, "before": ts.get(lab, []), "after": items} for lab, items in ns.items()
                if ts.get(lab) != items]
    return errs, added, dropped, reorders


def repeated_openers(md):
    """Bullets in one section that start with the same word ("Built" twice reads lazy)."""
    out = []
    for sec, blocks in parse(md)["sections"]:
        words = [plain(b).split()[0].lower() for blk in blocks if blk[0] == "entry" for b in blk[2] if plain(b).strip()]
        out += [f"{sec}: {w!r} opens {words.count(w)} bullets" for w in sorted(set(words)) if words.count(w) > 1]
    return out


# ---------- .md / .txt pair ----------

def sync(path):
    """Make <name>.md and <name>.txt identical (newer mtime wins, missing one is created). -> status string."""
    base = pathlib.Path(path)
    if base.suffix in (".md", ".txt"):
        base = base.with_suffix("")
    md, txt = base.with_suffix(".md"), base.with_suffix(".txt")
    if not md.exists() and not txt.exists():
        raise ValueError(f"neither {md} nor {txt} exists")
    if md.exists() != txt.exists():
        src, dst = (md, txt) if md.exists() else (txt, md)
    elif read(md) == read(txt):
        return "in sync"
    elif md.stat().st_mtime == txt.stat().st_mtime:
        raise ValueError(f"{md.name} and {txt.name} differ but have the same mtime; edit one and retry")
    else:
        src, dst = (md, txt) if md.stat().st_mtime > txt.stat().st_mtime else (txt, md)
    shutil.copy2(src, dst)
    return f"{src.suffix[1:]} -> {dst.suffix[1:]} (copied {src.name} over {dst.name})"


# ---------- selftest ----------

GOOD = """# Alex Rivera
alex@example.com | Springfield

## Work Experience
### **Engineer**, Acme || 2025
- Trained 20 networks in PyTorch

## Technical Skills
**Lang** – Python, C++
**Tools** – Git
"""


def selftest():
    import os, tempfile
    # validate
    r = validate(GOOD)
    assert r["ok"] and r["name"] == "Alex Rivera" and r["skill_labels"] == ["Lang", "Tools"], r
    assert r["skills"] == ["Python", "C++", "Git"] and r["sections"] == ["Work Experience", "Technical Skills"]
    r = validate(GOOD.replace("## Technical Skills\n**Lang** – Python, C++\n**Tools** – Git\n", ""))
    assert not r["ok"] and any("Technical Skills" in e for e in r["errors"]), r
    r = validate(GOOD.replace("**Tools** – Git", "Tools: Git"))
    assert not r["ok"] and any(e.startswith("line 10: skill line must look like **Label** – a, b, c") for e in r["errors"]), r
    r = validate(GOOD.replace("### **Engineer**, Acme || 2025\n", ""))
    assert not r["ok"] and any(e.startswith("line 5: bullet outside an entry") for e in r["errors"]), r
    r = validate("")
    assert not r["ok"] and r["errors"] == ["file is empty"]
    r = validate(GOOD.replace("|| 2025", ""))
    assert r["ok"] and any("no '|| date'" in w for w in r["warnings"]), r
    r = validate(GOOD.replace("## Technical Skills", "## technical skills"))
    assert r["ok"] and any("spelled" in w for w in r["warnings"]), r
    assert not validate("no heading\n## A\n")["ok"]
    with tempfile.TemporaryDirectory() as d:
        bad = pathlib.Path(d, "bad.md")
        bad.write_bytes(b"# Name\n\xff\xfe broken\n")
        r = validate_file(bad)
        assert not r["ok"] and "not UTF-8" in r["errors"][0], r
        assert not validate_file(pathlib.Path(d, "nope.md"))["ok"]
        # sync: newer wins, missing is created, equal is in sync
        md, txt = pathlib.Path(d, "r.md"), pathlib.Path(d, "r.txt")
        md.write_text("# A\n", encoding="utf-8")
        assert sync(md).startswith("md -> txt") and txt.read_text(encoding="utf-8") == "# A\n"
        assert sync(txt) == "in sync"
        txt.write_text("# B\n", encoding="utf-8")
        os.utime(txt, (md.stat().st_atime + 10, md.stat().st_mtime + 10))
        assert sync(pathlib.Path(d, "r")).startswith("txt -> md") and md.read_text(encoding="utf-8") == "# B\n"
        try:
            sync(pathlib.Path(d, "missing"))
            assert False
        except ValueError:
            pass
    # skills file
    sk, adj = parse_skills("## Skills\n- Python · main\n- C++\n- Git\n- SQL\n\n## Adjacent\n- Rust · near: C++ work\n")
    assert sk == {"Python": "main", "C++": "", "Git": "", "SQL": ""} and adj == {"Rust": "near: C++ work"}
    assert parse_skills(skills_from_template(GOOD))[0].keys() == {"Python", "C++", "Git"}
    allowed = set(sk) | set(adj)
    # ats
    assert ats(GOOD, GOOD, allowed) == ([], [], [], [])
    e, added, dropped, reo = ats(GOOD, GOOD.replace("Python, C++", "C++, SQL, Python").replace("– Git", "– Rust, Git"), allowed)
    assert e == [] and added == ["SQL", "Rust"] and dropped == [] and reo[0] == {"label": "Lang", "before": ["Python", "C++"],
           "after": ["C++", "SQL", "Python"]}, (e, added, reo)
    swapped = GOOD.replace("**Lang** – Python, C++\n**Tools** – Git", "**Tools** – Git\n**Lang** – Python, C++")
    assert ats(GOOD, swapped, allowed)[0] == [], "skill lines may be reordered"
    assert any("not in skills file" in x for x in ats(GOOD, GOOD.replace("Git", "Git, Zig"), allowed)[0])
    assert any("duplicate" in x for x in ats(GOOD, GOOD.replace("– Git", "– Git, Python"), allowed)[0])
    assert any("only Technical Skills" in x for x in ats(GOOD, GOOD.replace("20 networks", "25 networks"), allowed)[0])
    assert any("labels" in x for x in ats(GOOD, GOOD.replace("**Tools**", "**DevOps**"), allowed)[0])
    skills = GOOD[GOOD.index("## Technical"):]
    top = GOOD.replace(skills, "").replace("## Work", skills + "\n## Work")
    assert any("sections" in x for x in ats(GOOD, top, allowed)[0]), "skills stay where the template puts them"
    assert repeated_openers(GOOD) == []
    dup = GOOD.replace("- Trained 20 networks in PyTorch", "- Trained 20 networks in PyTorch\n- **Trained** a baseline")
    assert repeated_openers(dup) == ["Work Experience: 'trained' opens 2 bullets"], repeated_openers(dup)
    print("selftest ok")


def main(a):
    if a[:1] == ["--test"]:
        selftest()
    elif a[:1] == ["validate"] and len(a) in (2, 3):
        if pathlib.Path(a[1]).with_suffix(".txt").is_file():
            sync(a[1])
        res = validate_file(a[1])
        if res["ok"] and a[2:] == ["--render"]:
            import tempfile
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            from render import render
            with tempfile.TemporaryDirectory() as d:
                rr = render(a[1], pathlib.Path(d, "t.pdf"))
            if (rr["pages"] or 0) > 1:
                res["warnings"].append(f"your template is already over one page ({rr['pages']} pages)")
            elif not rr["ok"]:
                res["warnings"].append(f"test render failed: {rr['error']}")
        emit(res, res["ok"])
    elif a[:1] == ["ats"] and len(a) == 5 and a[3] == "--skills":
        try:
            allowed = set().union(*parse_skills(read(a[4])))
            errs, added, dropped, reo = ats(read(a[1]), read(a[2]), allowed)
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            emit({"ok": False, "errors": [f"{type(ex).__name__}: {ex}"], "added": [], "dropped": [], "reorders": []}, False)
        emit({"ok": not errs, "errors": errs, "added": added, "dropped": dropped, "reorders": reo}, not errs)
    elif a[:1] == ["sync"] and len(a) == 2:
        try:
            emit({"ok": True, "status": sync(a[1])})
        except (ValueError, OSError) as ex:
            emit({"ok": False, "status": "", "error": str(ex)}, False)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
