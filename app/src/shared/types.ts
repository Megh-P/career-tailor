export type Status = 'queued' | 'running' | 'done' | 'failed'

export interface Settings {
  templatesDir: string
  outputDir: string
  runsDir: string
  /** optional; empty = <templatesDir>/skills.md (tailor.py creates it from the template if missing) */
  skillsFile: string
  python: string
  agent: 'claude'
  model: string
  nameFormat: string
}

/** One template file in the templates folder, with its `resume.py validate` result. */
export interface TemplateInfo {
  path: string
  file: string
  name: string
  /** display title + icon: from templates.json in the templates folder, else guessed from the file name */
  title: string
  icon: string
  status: 'valid' | 'warnings' | 'invalid'
  errors: string[]
  warnings: string[]
}

export interface Check {
  id: 'python' | 'claude' | 'tectonic' | 'templates'
  label: string
  ok: boolean
  detail: string
  fix: string
}

/** One tailoring run: tailor.py's run record, plus app-side fields for live runs. */
export interface Run {
  id: string
  /** absolute path of the template .md */
  template: string
  status: Status
  company?: string
  role?: string
  folder?: string
  pdf?: string
  output?: string
  skills_added?: string[]
  new_adjacent?: string[]
  gaps?: string[]
  error?: string
  started?: string
  finished?: string
  /** first line of the pasted JD, for live runs before the company is known */
  title?: string
  hasSnapshot?: boolean
}

/** `resume.py ats` JSON */
export interface Ats {
  ok: boolean
  errors: string[]
  added: string[]
  dropped: string[]
  reorders: { label: string; before: string[]; after: string[] }[]
}

export interface Detail {
  ats: Ats | null
  atsAgainst: 'snapshot' | 'current template'
  template: string | null
  resume: string | null
  keywords: string | null
  changes: string | null
  /** new_adjacent skill -> its `near:` note from the skills file */
  near: Record<string, string>
}

export type OpenTarget = 'pdf' | 'folder' | 'output' | 'log' | 'templates' | 'runs' | 'docs'

export interface Api {
  list(): Promise<Run[]>
  tailor(template: string, jd: string): Promise<string>
  detail(id: string): Promise<Detail>
  open(target: OpenTarget, id?: string): Promise<string>
  onChange(cb: () => void): () => void
  getSettings(): Promise<Settings>
  saveSettings(s: Settings): Promise<Settings>
  pick(kind: 'folder' | 'file', current: string): Promise<string | null>
  openPath(p: string): Promise<string>
  templates(rescan?: boolean): Promise<TemplateInfo[]>
  onTemplates(cb: (t: TemplateInfo[]) => void): () => void
  preflight(): Promise<Check[]>
  installTectonic(): Promise<{ ok: boolean; output: string }>
  onTectonicProgress(cb: (line: string) => void): () => void
}
