## Rules for adding a skill (read before touching Technical Skills)

The resume may list a skill the owner has not written down yet, but never one they haven't used. The test: if an
interviewer asks "where did you use X?", the resume itself must already hold the answer.

Technical Skills holds three tiers:

1. Tools, on any fitting line. A tool has a proper name you install, import, run, or write in: a language, framework,
   library, tool, platform, database, or named protocol or query language (REST APIs, SQL).
2. Field-specific techniques, only on their own line: Deep Learning, Neural Networks, RAG, Fine-Tuning, AI Agents go
   on the ML/AI line, never on Databases & Tools or Languages. The skills file's `## Techniques (only on: <line>)`
   section lists them; the ats check refuses one on another line.
3. Broad concepts, never listed: a field or practice too wide to say anything, or one that isn't a tool but would
   have to sit on a tools line (Machine Learning or AI on the ML/AI line, Data Visualization, Data Analysis, Data
   Science, Version Control, APIs, Unit Testing, CI/CD, DevOps, Statistics). Not even when the posting asks for it word
   for word: list the tool that did that work instead (Data Visualization -> Matplotlib, Version Control -> Git, APIs
   -> REST APIs). The skills file's `## Concepts` section maps the common ones; the ats check refuses them.

A posting term that is neither a listed tool nor a listed technique: if it names a narrow method of the ML/AI field
that a bullet shows being done, add it to `## Techniques`; if it is broad, add it to `## Concepts` as
`- <Concept> -> <tools>` and list the tool. Never put a technique or concept in `## Skills` or `## Adjacent`.

A posting tool that is not in `## Skills` of the skills file may be added only as one of these four kinds. Append it
to `## Adjacent` as `- <Tool as the posting spells it> · <kind>: <evidence>`, then use it:

- `same as`: another spelling or name of a listed tool. `Postgres · same as: PostgreSQL`, `React.js · same as: React`.
- `part of`: using a listed tool means using this one. `C · part of: C++ (C/C++ repositories)`, `SQL · part of: SQLite`,
  `JavaScript · part of: TypeScript`, `GitHub · part of: Git and GitHub Actions CI`.
- `describes`: a named protocol or standard the work already uses. `REST APIs · describes: FastAPI server`,
  `Bash · describes: CLI tooling and CI scripts`.
- `named in`: the tool appears in a bullet or entry header but not in Technical Skills. `Cursor · named in: Tycho bullet`.

The evidence must point at real text in the template (or a skill already in `## Skills`). If you can't quote it, it
isn't evidence.

Never add (these are gaps; report them, don't list them):
- A different tool, framework, language, platform, or product than the one used, even in the same category:
  TensorFlow because of PyTorch, Angular because of React, Power BI because of Tableau, Jenkins or GitLab because of
  GitHub Actions, Kubernetes because of Docker, AWS because of Supabase, Rust or Go because of C++.
- A skill justified by "similar to", "sibling of", "could learn it", "transferable", or a class the owner merely took.
- A technique the bullets don't show being done (A/B Testing because of evaluation work, VAEs because a pretrained
  model happens to use one).
- Certifications, clearances, or years of experience.

When unsure, it's a gap. A missing keyword costs one ATS filter; a fabricated one costs the interview.
