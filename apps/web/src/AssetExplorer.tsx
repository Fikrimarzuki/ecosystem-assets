import { useEffect, useMemo, useState, type MouseEvent } from 'react'
import { ArrowUpRight, FileType, Grid2X2, List, Search, SlidersHorizontal } from 'lucide-react'
import { Badge, Button, Card, EmptyState, Input } from './components'
import type { PublicMedia, PublicShowcase } from './catalog'
import { defaultExplorerState, parseExplorerQuery, previewFormats, projectName, selectShowcases, serializeExplorerQuery, showcaseUrl, type ExplorerState } from './explorer'
import { useLanguage } from './i18n'

const previewable = new Set(['png','svg','ico','jpg','jpeg','webp','gif','avif'])
export function AssetPreview({ media }: { media?: PublicMedia }) {
  const { t } = useLanguage()
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [media?.url])
  return <div className="asset-preview">
    {media && previewable.has(media.format) && !failed ? <img src={media.url} alt="" loading="lazy" onError={() => setFailed(true)} /> :
      <span className="asset-preview-fallback" role="img" aria-label={!media ? t('No preview available') : failed ? t('Preview unavailable') : t('{format} preview unavailable', { format: media.format.toUpperCase() })}><FileType size={29} strokeWidth={1.5} /><small>{!media ? t('NO PREVIEW') : failed ? t('PREVIEW UNAVAILABLE') : media.format.toUpperCase()}</small></span>}
  </div>
}

export function ShowcaseCard({ showcase, view, navigate }: { showcase: PublicShowcase; view: 'grid' | 'list'; navigate: (showcase: PublicShowcase) => void }) {
  const { t } = useLanguage()
  const href = showcaseUrl(showcase)
  const onClick = (event: MouseEvent<HTMLAnchorElement>) => {
    if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
    event.preventDefault(); navigate(showcase)
  }
  return <article className={`asset-card asset-card-${view}`}>
    <AssetPreview media={showcase.media[0]} />
    <div className="asset-card-body"><div className="asset-card-heading"><div><p className="eyebrow">{projectName(showcase.projectId)} / {showcase.category}</p><h2>{showcase.title}</h2></div><Badge tone={showcase.publication === 'downloadable' ? 'success' : 'accent'}>{t(showcase.publication === 'downloadable' ? 'Downloadable' : 'Showcase')}</Badge></div>
      <p className="asset-card-description">{showcase.description}</p>
      {showcase.tags?.length ? <div className="asset-tags">{showcase.tags.map(tag => <span key={tag}>{tag}</span>)}</div> : null}
      <div className="asset-card-foot"><span>{t(showcase.media.length === 1 ? '{count} view' : '{count} views', { count: showcase.media.length })} · {previewFormats(showcase).join(', ') || t('No preview format')}</span><a href={href} onClick={onClick} aria-label={t('View {title}', { title: showcase.title })}>{t('View asset')} <ArrowUpRight size={16} /></a></div>
    </div>
  </article>
}

const unique = (values: string[]) => [...new Set(values)].sort((a, b) => a.localeCompare(b))
function useExplorerState() {
  const [state, setState] = useState(() => parseExplorerQuery(window.location.search))
  useEffect(() => {
    const onPop = () => setState(parseExplorerQuery(window.location.search))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  const update = (change: Partial<ExplorerState>) => {
    const next = { ...state, ...change }
    const query = serializeExplorerQuery(next)
    window.history.pushState(null, '', `${window.location.pathname}${query ? `?${query}` : ''}`)
    setState(next)
  }
  return { state, update }
}

export function AssetExplorer({ showcases, lockedProject, navigate }: { showcases: PublicShowcase[]; lockedProject?: string; navigate: (showcase: PublicShowcase) => void }) {
  const { t } = useLanguage()
  const { state, update } = useExplorerState()
  const scoped = useMemo(() => lockedProject ? showcases.filter(item => item.projectId === lockedProject) : showcases, [showcases, lockedProject])
  const selected = useMemo(() => selectShowcases(scoped, state, lockedProject), [scoped, state, lockedProject])
  const projects = unique(showcases.map(item => item.projectId))
  const categories = unique(scoped.map(item => item.category))
  const formats = unique(scoped.flatMap(item => item.media.map(media => media.format)))
  const active = Boolean(state.q || (!lockedProject && state.project) || state.category || state.format)
  const clear = () => update({ ...defaultExplorerState, sort: state.sort, view: state.view })
  return <>
    <Card className="explorer-controls">
      <label className="search-field"><Search size={19} aria-hidden="true" /><span className="sr-only">{t('Search public showcases')}</span><Input type="search" value={state.q} onChange={event => update({ q: event.target.value })} placeholder={t('Search titles, stories, projects, tags')} /></label>
      <div className="explorer-filters"><SlidersHorizontal size={17} aria-hidden="true" />
        {!lockedProject && <label><span className="sr-only">{t('Project')}</span><select aria-label={t('Project')} value={state.project} onChange={event => update({ project: event.target.value })}><option value="">{t('All projects')}</option>{projects.map(project => <option value={project} key={project}>{projectName(project)}</option>)}</select></label>}
        <label><span className="sr-only">{t('Category')}</span><select aria-label={t('Category')} value={state.category} onChange={event => update({ category: event.target.value })}><option value="">{t('All categories')}</option>{categories.map(category => <option value={category} key={category}>{category}</option>)}</select></label>
        <label><span className="sr-only">{t('Format')}</span><select aria-label={t('Format')} value={state.format} onChange={event => update({ format: event.target.value })}><option value="">{t('All preview formats')}</option>{formats.map(format => <option value={format} key={format}>{format.toUpperCase()}</option>)}</select></label>
        <label><span className="sr-only">{t('Sort')}</span><select aria-label={t('Sort')} value={state.sort} onChange={event => update({ sort: event.target.value as ExplorerState['sort'] })}><option value="name-asc">{t('Name A–Z')}</option><option value="name-desc">{t('Name Z–A')}</option><option value="size-asc">{t('Smallest preview first')}</option><option value="size-desc">{t('Largest preview first')}</option></select></label>
      </div>
      <div className="explorer-options"><span role="status">{t(selected.length === 1 ? '{count} showcase' : '{count} showcases', { count: selected.length })}</span>{active && <Button variant="ghost" onClick={clear}>{t('Clear filters')}</Button>}<div className="view-switch" role="group" aria-label={t('View')}><button type="button" aria-label={t('Grid view')} aria-pressed={state.view === 'grid'} onClick={() => update({ view: 'grid' })}><Grid2X2 size={17} /></button><button type="button" aria-label={t('List view')} aria-pressed={state.view === 'list'} onClick={() => update({ view: 'list' })}><List size={18} /></button></div></div>
    </Card>
    {scoped.length === 0 ? <Card className="page-panel"><EmptyState title={t('The gallery is taking shape')} description={t('There are no public showcases yet. Selected work will appear here after preview and rights approval.')} /></Card> : selected.length === 0 ? <Card className="page-panel"><EmptyState title={t('No matching assets')} description={t('Try another search or filter. Only published showcases can appear here.')} action={<Button variant="secondary" onClick={clear}>{t('Clear filters')}</Button>} /></Card> : <div className={`asset-results asset-results-${state.view}`}>{selected.map(item => <ShowcaseCard key={item.id} showcase={item} view={state.view} navigate={navigate} />)}</div>}
  </>
}
