# Template format

A template is one plain markdown file holding your whole one-page resume. Career Tailor only ever rewrites its
`## Technical Skills` section; everything else is copied through unchanged and checked afterwards.
See `examples/templates/example-swe.md` for a complete example.

## Line types

| Line | Meaning |
|------|---------|
| `# Name` | First line. Your name. |
| lines before the first `## ` | Contact line(s): email, phone, links. Free text, usually one line separated by `\|`. |
| `## Section` | A section heading (Education, Work Experience, ...). |
| `### **Title**, Org \|\| Mon YYYY – Mon YYYY` | An entry. Text before `\|\|` is the left side (bold the title), text after is the date. |
| `- text` | A bullet. Must come after a `###` entry. |
| any other line | A paragraph (used for skill lines). |

Blank lines are ignored. Use `**bold**` for key metrics and `*italic*` for emphasis. Use the en dash `–` in date
ranges and skill lines.

```markdown
# Alex Rivera
alex.rivera@example.com | (555) 010-4721 | github.com/alexrivera-example

## Work Experience
### **Software Engineering Intern**, Brightwave Logistics || May 2024 – Aug 2024
- Built a route-batching service that cut dispatcher planning time by **35%**

## Technical Skills
**Languages & Frameworks** – Python, C++, TypeScript
```

## Required structure

- `# Name` is the first line.
- At least one `## ` section.
- A section named exactly `## Technical Skills` (matched case-insensitively; a different case gives a warning).
  Put it **last**: it is the only section the app edits, and the diff reads best that way.
- Technical Skills contains skill lines, one per category, in the form `**Label** – item, item, item`.
  The separator is an en dash (`–`); `-` and `:` are also accepted. Items are comma separated.
- Keep the labels you want (for example `Languages & Frameworks`, `Tools & Platforms`, `Concepts`). The tailoring
  agent may add, drop, and reorder items inside a line but cannot rename, add, or remove labels.
- `### ` entries should have a `||` date. A missing one is a warning, not an error.

## What the app checks after a run

The rewritten resume must equal your template everywhere except Technical Skills:

- header and contact lines unchanged
- sections not added, removed, or reordered
- every other section identical
- skill labels unchanged
- no duplicate skills
- every skill is in your skills file (`skills.md`)

If a check fails the run is marked failed and the problem is shown in the detail view.

## Validation

```
python backend/resume.py validate <template.md> [--render]
```

Prints one JSON object (`ok`, `errors`, `warnings`, `name`, `sections`, `skill_labels`, `skills`) and exits 0 when
valid, 1 when not. `--render` also compiles it and warns when it is more than one page. In general terms, errors are:

- file is empty or not UTF-8
- first line is not `# Name`
- no `## ` sections
- no `## Technical Skills` section
- skill lines not in `**Label** – a, b` form
- a bullet that is not under a `###` entry

Warnings are things like a `###` entry with no `||` date, a differently cased Technical Skills heading, duplicate
skills, filler words ("leverage", "spearhead", ...), two bullets in one section opening with the same word, or, with
`--render`, a template that renders to more than one page.

## skills.md

The allowlist of skills the agent may use. Every skill in your Technical Skills section should be listed, because
the agent can only reorder or add skills that appear in this file. If you do not point the app at a skills file,
one is generated from your template's skill lines.

```markdown
## Skills
- Python · Brightwave route-batching service
- Docker · dev environment at Brightwave

## Adjacent
- MySQL · near: PostgreSQL and SQLite in projects
```

- `## Skills`: things you have actually done. One per line, `- Skill · evidence note`. The evidence note is for
  you; only the skill name is matched.
- `## Adjacent`: skills you have not used directly but are close to something you have. The agent may add one when a
  job asks for it, and reports it as an adjacent addition so you can review it before applying. Write what it is
  near, for example `- Go · near: C++ systems work`. Be honest here; you are the one answering interview questions.

You can split skills into several `##` sections (`## Languages`, `## Tools`, ...); every section counts as skills
except `## Adjacent`, and except sections whose title contains "domain", "not listed", or "ignore" (use those for
notes). Anything in neither list is never added.

## Convert your existing resume

Give this prompt to Claude Code, Codex, Cursor, or any coding agent, in a folder that contains your resume
(PDF or DOCX) and a copy of this repo (or at least `backend/` and `docs/TEMPLATE_FORMAT.md`):

```text
Convert my resume file (<path to my PDF or DOCX>) into a Career Tailor markdown template.

Read docs/TEMPLATE_FORMAT.md and examples/templates/example-swe.md first and follow that dialect exactly:
- "# Name" first, then the contact line, then "## Section" headings.
- Entries as "### **Title**, Org || Mon YYYY – Mon YYYY" with "- bullet" lines under them.
- Keep my wording. Do not invent, rewrite, or embellish anything. Bold key metrics with **...**.
- Put "## Technical Skills" LAST, with lines like "**Languages & Frameworks** – A, B, C".
- Use the en dash in date ranges and skill lines.

Save it as <templates folder>/<name>.md. Also write a skills.md next to it with a "## Skills" section
listing every skill in my Technical Skills section as "- Skill · evidence note" (name the project or job
that shows it), and an empty "## Adjacent" section.

Then run: python backend/resume.py validate <templates folder>/<name>.md
Fix every error and re-run until it prints "ok": true. Tell me about any warnings, and flag anything you
were unsure about so I can check it against my original.
```

## Tips

- Keep it to one page. `validate --render` warns when the template renders to two, and tailoring never shortens other sections.
- Put Technical Skills last. It is the only section the app edits.
- Make one template per role family (for example SWE, ML, PM) with different bullets and skill labels, then pick the
  closest one per job.
- Put the strongest keywords for your target roles in Technical Skills; the agent reorders them to match each posting.
- Bullets around 150 to 220 characters read well; bold only the key numbers.
- Review the diff in the run detail view before sending any resume.
- Prefer editing in a plain `.txt`? Keep a `<name>.txt` next to `<name>.md` with the same content. Whichever of the two
  you saved last is copied over the other before every validation and run, so editing either one works.
