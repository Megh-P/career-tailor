import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import type { Check, Run, TemplateInfo } from '../shared/types'
import { RunDetail } from './Detail'
import { SettingsView, SetupView, StatusBadge, TemplatesView } from './Views'
import { Icon, PageHead, elapsed, errText, runTitle, templateName, tplIcon, when, type IconName } from './ui'

type View = 'compose' | 'templates' | 'settings' | 'setup' | { run: string }

export function App() {
  const [runs, setRuns] = useState<Run[] | null>(null)
  const [templates, setTemplates] = useState<TemplateInfo[] | null>(null)
  const [checks, setChecks] = useState<Check[] | null>(null)
  const [view, setView] = useState<View>('compose')
  const [, setTick] = useState(0)

  const reload = useCallback(() => window.api.list().then(setRuns), [])
  useEffect(() => { reload(); return window.api.onChange(reload) }, [reload])
  useEffect(() => { window.api.templates().then(setTemplates); return window.api.onTemplates(setTemplates) }, [])

  const recheck = useCallback(async () => {
    setChecks(null)
    const c = await window.api.preflight()
    setChecks(c)
    window.api.templates().then(setTemplates)
    return c
  }, [])
  useEffect(() => { recheck().then((c) => { if (c.some((x) => !x.ok)) setView('setup') }) }, [recheck])

  const live = runs?.some((r) => r.status === 'running' || r.status === 'queued')
  useEffect(() => {
    if (!live) return
    const t = setInterval(() => setTick((n) => n + 1), 1000)
    return () => clearInterval(t)
  }, [live])

  const selected = typeof view === 'object' ? view.run : null
  const run = runs?.find((r) => r.id === selected)
  const issues = checks?.filter((c) => !c.ok).length ?? 0
  const nav = (v: View, icon: IconName, label: string, badge?: ReactNode) => (
    <button className={`nav-item ${view === v ? 'active' : ''}`} onClick={() => setView(v)} aria-current={view === v ? 'page' : undefined}>
      <Icon name={icon} size={15} />{label}{badge}
    </button>
  )

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="mark" aria-hidden="true">CT</span>
          <span className="brand-name">Career Tailor</span>
        </div>
        <nav className="nav" aria-label="Main">
          {nav('compose', 'plus', 'New tailoring')}
          {nav('templates', 'file', 'Templates', templates?.length ? <span className="count">{templates.length}</span> : null)}
          {nav('settings', 'settings', 'Settings')}
          {nav('setup', 'wrench', 'Setup', issues ? <span className="count count-bad">{issues}</span> : null)}
        </nav>
        <div className="side-label">History{runs?.length ? <span className="count">{runs.length}</span> : null}</div>
        <nav className="runs" aria-label="Runs">
          {runs === null && [0, 1, 2].map((i) => <div key={i} className="run-item skeleton" />)}
          {runs?.length === 0 && <p className="side-empty">No runs yet.</p>}
          {runs?.map((r) => (
            <button key={r.id} className={`run-item ${r.id === selected ? 'selected' : ''}`} onClick={() => setView({ run: r.id })}
              aria-current={r.id === selected ? 'page' : undefined}>
              <span className={`dot dot-${r.status}`} aria-label={r.status} />
              <span className="run-text">
                <span className="run-title" title={runTitle(r)}>{r.company || r.title || 'Untitled posting'}</span>
                {r.role && <span className="run-role" title={r.role}>{r.role}</span>}
                <span className="run-sub">
                  <span className="tag">{templateName(r.template)}</span>
                  {r.applied?.ok && <span className="tag tag-applied">applied</span>}
                  {r.status === 'running' ? `running ${elapsed(r.started)}` : r.status === 'queued' ? 'queued' : r.status === 'failed' ? 'failed' : when(r.finished || r.started)}
                </span>
              </span>
            </button>
          ))}
        </nav>
        <button className="btn btn-ghost side-foot" onClick={() => window.api.open('output')}>
          <Icon name="folder" /> Output folder
        </button>
      </aside>

      <main className="main">
        {run ? <RunDetail key={run.id} run={run} />
          : view === 'templates' ? <TemplatesView templates={templates} onRescan={() => window.api.templates(true).then(setTemplates)} />
          : view === 'settings' ? <SettingsView onSaved={recheck} />
          : view === 'setup' ? <SetupView checks={checks} onRecheck={recheck} go={setView} />
          : <Composer templates={templates} onQueued={(id) => setView({ run: id })} go={setView} />}
      </main>
    </div>
  )
}

const LAST = 'ct.template'
const AUTO = 'auto' // tailor.py --template auto: the agent picks the template
const RANK = { valid: 0, warnings: 1, invalid: 2 }
const remembered = () => { try { return localStorage.getItem(LAST) } catch { return null } }

function Composer({ templates, onQueued, go }: { templates: TemplateInfo[] | null; onQueued: (id: string) => void; go: (v: View) => void }) {
  const [jd, setJd] = useState('')
  const [pick, setPick] = useState<string | null>(remembered)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => ref.current?.focus(), [])

  const usable = templates?.filter((t) => t.status !== 'invalid').sort((a, b) => RANK[a.status] - RANK[b.status]) ?? []
  const auto = pick === AUTO && usable.length > 1 // auto needs something to choose between
  const template = auto ? { path: AUTO } : usable.find((t) => t.path === pick) ?? usable[0]
  const choose = (p: string) => { setPick(p); try { localStorage.setItem(LAST, p) } catch { /* private mode */ } }

  const words = jd.trim() ? jd.trim().split(/\s+/).length : 0
  const submit = async () => {
    if (!jd.trim() || busy || !template) return
    setBusy(true)
    setErr('')
    try {
      const id = await window.api.tailor(template.path, jd)
      setJd('')
      onQueued(id)
    } catch (e) {
      setErr(errText(e))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); submit() } }
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  })

  return (
    <div className="page composer">
      <PageHead title="Tailor a resume" sub="Paste a job description and pick a template. The agent rewrites only the Technical Skills section; you review every change here." />
      <div className="composer-grid">
        <div className="jd-card">
          <label htmlFor="jd" className="field-label">Job description</label>
          <textarea id="jd" ref={ref} value={jd} onChange={(e) => setJd(e.target.value)} spellCheck={false}
            placeholder="Paste the full posting: title, company, responsibilities, requirements…" />
          <div className="jd-foot">
            <span>{words ? `${words.toLocaleString()} words` : 'Empty'}</span>
            {jd && <button className="link" onClick={() => { setJd(''); ref.current?.focus() }}>Clear</button>}
          </div>
        </div>
        <div className="side-panel">
          <div className="field-label" id="tpl-label">Template</div>
          {templates === null ? <div className="tpl skeleton" />
            : !templates.length ? (
              <div className="empty-mini">
                <p>No templates yet.</p>
                <button className="link" onClick={() => go('templates')}>Add a template</button>
              </div>
            ) : (
              <div className="tpl-list" role="radiogroup" aria-labelledby="tpl-label">
                {usable.length > 1 && (
                  <button role="radio" aria-checked={auto} className={`tpl tpl-auto ${auto ? 'on' : ''}`} onClick={() => choose(AUTO)}
                    title="An extra agent call reads the posting and picks the best-fitting template">
                    <span className="tpl-icon" aria-hidden="true"><Icon name="wand" size={17} /></span>
                    <span className="tpl-text">
                      <span className="tpl-name">Auto</span>
                      <span className="tpl-file">Picks the best template for the posting</span>
                    </span>
                  </button>
                )}
                {[...templates].sort((a, b) => RANK[a.status] - RANK[b.status]).map((t) => {
                  const on = t.path === template?.path
                  const bad = t.status === 'invalid'
                  return (
                    <button key={t.path} role="radio" aria-checked={on} disabled={bad}
                      className={`tpl ${on ? 'on' : ''}`} onClick={() => choose(t.path)}
                      title={bad ? `Invalid: ${t.errors[0] ?? ''}` : t.path}>
                      <span className="tpl-icon" aria-hidden="true"><Icon name={tplIcon(t.icon)} size={17} /></span>
                      <span className="tpl-text">
                        <span className="tpl-name">{t.title}</span>
                        <span className="tpl-file mono">{t.file}</span>
                      </span>
                      {t.status !== 'valid' && <StatusBadge t={t} />}
                    </button>
                  )
                })}
              </div>
            )}
          {templates?.some((t) => t.status === 'invalid') && (
            <button className="link small" onClick={() => go('templates')}>Why are some templates disabled?</button>
          )}
          <button className="btn btn-primary btn-lg" disabled={!jd.trim() || busy || !template} onClick={submit}>
            {busy && <Icon name="spinner" className="spin" />}
            Tailor resume
            <kbd>Ctrl ↵</kbd>
          </button>
          {err && <div className="alert alert-danger" role="alert"><Icon name="alert" />{err}</div>}
          <ul className="notes">
            <li><Icon name="clock" size={14} />Takes 1–4 minutes. Up to 3 run at once; the rest queue.</li>
            <li><Icon name="shield" size={14} />Only Technical Skills may change; an integrity check verifies it.</li>
            <li><Icon name="folder" size={14} />The PDF is copied to your output folder.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
