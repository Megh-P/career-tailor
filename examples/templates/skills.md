# Skills allowlist

The tailoring agent may only put skills from this file into the Technical Skills section.
Format: `- Skill · evidence note` (the text after the dot is for you; only the skill name is matched).

Skills: things you have actually done. Listed in the resume, or backed by a project or job.
Adjacent: skills you did use but haven't written down, each with a kind and the evidence:
`same as` (another name), `part of` (using a listed skill means using it), `describes` (names work a bullet
shows), `named in` (the tool appears in a bullet). Never a different tool you haven't used: Go is not
"near" C++. See backend/prompts/skill-rules.md.

Anything not in either list is never added. Edit freely.

## Skills
- Python · Brightwave route-batching service, TA autograder
- C++ · Quill compiler
- TypeScript · TrailSync tile cache
- JavaScript · TrailSync
- Java · coursework, Data Structures TA
- SQL · Brightwave PostgreSQL, TrailSync SQLite
- React · TrailSync UI
- Node.js · TrailSync backend
- React Native · TrailSync
- Git · all projects
- Docker · Brightwave dev environment
- PostgreSQL · Brightwave route-batching service
- SQLite · TrailSync offline storage
- Kafka · Brightwave inventory pipeline
- GitHub Actions · Brightwave CI migration check
- Linux · daily development
- LLVM · Quill backend
- Distributed Systems · coursework, Kafka pipeline
- Data Structures · TA role
- Algorithms · TA role, coursework
- Compilers · Quill
- REST APIs · Brightwave, TrailSync
- Unit Testing · Brightwave integration tests
- CI/CD · GitHub Actions

## Adjacent
- Postgres · same as: PostgreSQL
- C · part of: C++ (Quill compiler)
- Data Pipelines · describes: Kafka inventory pipeline at Brightwave
- Event Streaming · describes: Kafka inventory pipeline at Brightwave
