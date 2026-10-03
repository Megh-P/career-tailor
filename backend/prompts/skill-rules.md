## Rules for adding a skill (read before touching Technical Skills)

The resume may list a skill the owner has not written down yet, but never one they haven't used. The test: if an
interviewer asks "where did you use X?", the resume itself must already hold the answer.

A posting skill that is not in `## Skills` of the skills file may be added only as one of these four kinds. Append it
to `## Adjacent` as `- <Skill as the posting spells it> · <kind>: <evidence>`, then use it:

- `same as`: another spelling or name of a listed skill. `Postgres · same as: PostgreSQL`, `LLMs · same as: LLM Integration`.
- `part of`: using a listed skill means using this one. `C · part of: C++ (C/C++ repositories)`, `SQL · part of: SQLite`,
  `JavaScript · part of: TypeScript`, `GitHub · part of: Git and GitHub Actions CI`.
- `describes`: a technique or umbrella term for work a bullet already shows. `Unit Testing · describes: pytest suites (Tycho)`,
  `Web Scraping · describes: scraped TransLoc GPS data (StingerDelay)`.
- `named in`: the tool or term appears in a bullet or entry header but not in Technical Skills. `Cursor · named in: Tycho bullet`.

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
