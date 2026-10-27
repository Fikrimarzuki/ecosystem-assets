import { useEffect, useState, type MouseEvent } from 'react'
import {
  Activity, ArrowRight, ArrowUpRight, BookOpen, Check, CircleHelp, FileType, Folder,
  Info, Layers, LayoutDashboard, LockKeyhole, Menu, Moon, Search, ShieldCheck,
  Sun, X,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, LoadingState, PageHeader } from './components'
import { usePublicCatalog, type PublicShowcase, type PublicCatalog } from './catalog'
import { useTheme } from './theme'
import { AssetExplorer, AssetPreview } from './AssetExplorer'
import { projectCollections, projectName, showcaseUrl } from './explorer'
import { ShowcaseDetail } from './ShowcaseDetail'
import { useLanguage } from './i18n'

const SUPPORT_URL = 'https://support.fikrimarzuki.work/'
const GATEWAY_URL = 'https://fikrimarzuki.work/'

type Route = string
const nav: { path: Route; label: string; icon: LucideIcon }[] = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/explore', label: 'Explore', icon: Search },
  { path: '/collections', label: 'Collections', icon: Folder },
  { path: '/health', label: 'Asset Health', icon: Activity },
  { path: '/about', label: 'About', icon: Info },
]

function routeFromLocation(): Route | null {
  const path = window.location.pathname.replace(/\/$/, '') || '/'
  return nav.find(item => item.path === path)?.path ?? (/^\/collections\/[A-Za-z0-9_-]+$/.test(path) || /^\/assets\/[A-Za-z0-9_-]+\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(path) ? path : null)
}

function useRoute() {
  const [route, setRoute] = useState<Route | null>(routeFromLocation)
  useEffect(() => {
    const onPop = () => setRoute(routeFromLocation())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  const navigate = (path: Route) => {
    if (window.location.pathname !== path || window.location.search) window.history.pushState(null, '', path)
    setRoute(path)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }
  return { route, navigate }
}

function NavItem({ item, active, navigate, close }: { item: typeof nav[number]; active: boolean; navigate: (path: Route) => void; close?: () => void }) {
  const { t } = useLanguage()
  const Icon = item.icon
  const onClick = (event: MouseEvent<HTMLAnchorElement>) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
    event.preventDefault()
    navigate(item.path)
    close?.()
  }
  return <a href={item.path} onClick={onClick} className={`nav-item ${active ? 'is-active' : ''}`} aria-current={active ? 'page' : undefined}>
    <Icon size={18} strokeWidth={1.8} aria-hidden="true" /><span>{t(item.label)}</span>{active && <span className="nav-active-mark" aria-hidden="true" />}
  </a>
}

function ExternalNavItem({ href, label, icon: Icon, close }: { href: string; label: string; icon: LucideIcon; close?: () => void }) {
  const { t } = useLanguage()
  return <a className="nav-item" href={href} onClick={close}><Icon size={18} strokeWidth={1.8} aria-hidden="true" /><span>{t(label)}</span><ArrowUpRight className="nav-external-icon" size={14} aria-hidden="true" /></a>
}

function Brand() {
  return <div className="brand"><div className="brand-mark" aria-hidden="true"><span /><span /><span /></div><div><strong>Asset Studio</strong><small>FM WORK / ECOSYSTEM</small></div></div>
}

function Sidebar({ route, navigate }: { route: Route | null; navigate: (path: Route) => void }) {
  const { t } = useLanguage()
  return <aside className="sidebar"><Brand />
    <div className="sidebar-content"><p className="nav-section-label">{t('WORKSPACE')}</p><nav aria-label={t('Primary navigation')}>{nav.slice(0, 4).map(item => <NavItem key={item.path} item={item} active={route === item.path || (item.path === '/collections' && Boolean(route?.startsWith('/collections/'))) || (item.path === '/explore' && Boolean(route?.startsWith('/assets/')))} navigate={navigate} />)}</nav>
      <p className="nav-section-label nav-section-secondary">{t('INFORMATION')}</p><nav aria-label={t('INFORMATION')}><NavItem item={nav[4]} active={route === '/about'} navigate={navigate} /><ExternalNavItem href={SUPPORT_URL} label="Support" icon={CircleHelp} /><ExternalNavItem href={GATEWAY_URL} label="More projects" icon={Layers} /></nav>
    </div>
    <div className="sidebar-bottom"><div className="sidebar-note-icon"><ShieldCheck size={18} /></div><div><strong>{t('Publication first')}</strong><p>{t('Only approved assets appear in this space.')}</p></div></div>
    <div className="sidebar-foot">FM WORK <span>·</span> ASSET SYSTEM</div>
  </aside>
}

function AppHeader({ route, theme, toggleTheme, menuOpen, setMenuOpen, catalogStatus }: { route: Route | null; theme: 'light' | 'dark'; toggleTheme: () => void; menuOpen: boolean; setMenuOpen: (open: boolean) => void; catalogStatus: 'loading' | 'error' | 'ready' }) {
  const { language, setLanguage, t } = useLanguage()
  const title = route?.startsWith('/collections/') ? 'Collection' : route?.startsWith('/assets/') ? 'Showcase' : nav.find(item => item.path === route)?.label ?? 'Page not found'
  return <header className="app-header">
    <div className="header-left"><button className="icon-button mobile-menu-button" type="button" aria-label={t(menuOpen ? 'Close navigation' : 'Open navigation')} aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={20} /> : <Menu size={20} />}</button><span className="header-workspace">{t('Workspace')}</span><span className="header-slash">/</span><strong>{t(title)}</strong></div>
    <div className="header-right"><span className={`catalog-status status-${catalogStatus}`}><span className="status-dot" />{t('Public catalog')}</span><span className="header-divider" /><div className="language-switch" role="group" aria-label={t('Language')}><button type="button" lang="en" aria-pressed={language === 'en'} onClick={() => setLanguage('en')}>EN</button><button type="button" lang="id" aria-pressed={language === 'id'} onClick={() => setLanguage('id')}>ID</button></div><button className="icon-button theme-button" type="button" onClick={toggleTheme} aria-label={t(theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode')} title={t(theme === 'light' ? 'Dark mode' : 'Light mode')}>{theme === 'light' ? <Moon size={19} /> : <Sun size={19} />}</button></div>
  </header>
}

function StatCard({ label, value, detail, icon: Icon }: { label: string; value: string; detail: string; icon: LucideIcon }) {
  return <Card className="stat-card"><div className="stat-top"><span>{label}</span><span className="stat-icon"><Icon size={18} strokeWidth={1.8} /></span></div><strong>{value}</strong><small>{detail}</small></Card>
}

function Overview({ catalog, navigate }: { catalog: PublicCatalog; navigate: (path: Route) => void }) {
  const { t } = useLanguage()
  const formats = [...new Set(catalog.showcases.flatMap(item => item.media.map(file => file.format.toUpperCase())))].sort()
  return <>
    <div className="overview-hero"><div className="hero-copy"><p className="eyebrow"><span className="eyebrow-line" /> {t('THE PUBLIC ASSET SPACE')}</p><h1>{t('Everything creative,')}<br /><em>{t('beautifully organized.')}</em></h1><p>{t('A considered home for the visual assets behind FM Work. Browse what has been approved, understand where it belongs, and find the right file with confidence.')}</p><div className="hero-actions"><Button onClick={() => navigate('/explore')}>{t('Explore assets')} <ArrowRight size={17} /></Button><Button variant="secondary" onClick={() => navigate('/about')}>{t('How it works')} <ArrowUpRight size={16} /></Button></div></div><div className="hero-art" aria-hidden="true"><div className="art-grid" /><div className="art-tile art-tile-back"><span className="art-dot" /><span className="art-stripe" /></div><div className="art-tile art-tile-front"><div className="art-sun" /><div className="art-hill art-hill-one" /><div className="art-hill art-hill-two" /></div><div className="art-orbit art-orbit-one" /><div className="art-orbit art-orbit-two" /><div className="art-label">{t('CURATED / PUBLISHED')}</div></div></div>
    <div className="section-heading"><div><p className="eyebrow">{t('AT A GLANCE')}</p><h2>{t('Studio overview')}</h2></div><Badge tone="accent">{t('Live public catalog')}</Badge></div>
    <div className="stats-grid"><StatCard label={t('Showcases')} value={String(catalog.showcases.length)} detail={t('Curated public entries')} icon={Layers} /><StatCard label={t('Collections')} value={String(projectCollections(catalog.showcases).length)} detail={t('Projects with public work')} icon={Folder} /><StatCard label={t('Preview formats')} value={String(formats.length)} detail={formats.length ? formats.join(', ') : t('No formats yet')} icon={FileType} /><StatCard label={t('Catalog version')} value={`v${catalog.schemaVersion}`} detail={t('Structured public data')} icon={BookOpen} /></div>
    <div className="content-grid"><Card className="featured-panel"><div className="panel-top"><div><p className="eyebrow">{t('THE GALLERY')}</p><h2>{t('Featured work')}</h2></div><span className="panel-kicker">{t('01 / DISCOVER')}</span></div>{catalog.showcases.length === 0 ? <div className="featured-empty"><div className="featured-visual" aria-hidden="true"><div className="visual-sheet sheet-one" /><div className="visual-sheet sheet-two" /><div className="visual-sheet sheet-three"><div className="visual-plus">+</div></div></div><div className="featured-copy"><Badge>{t('Collection in progress')}</Badge><h3>{t('A clean canvas, ready for what’s next.')}</h3><p>{t('No showcases have been approved for public display yet. When they are, you’ll find them here.')}</p><Button variant="secondary" onClick={() => navigate('/about')}>{t('See our publishing approach')} <ArrowRight size={16} /></Button></div></div> : <div className="published-list">{catalog.showcases.slice(0, 4).map(item => <ShowcaseRow key={item.id} showcase={item} navigate={navigate} />)}<Button variant="secondary" onClick={() => navigate('/explore')}>{t('View all showcases')} <ArrowRight size={16} /></Button></div>}</Card>
      <Card className="principles-panel"><div className="panel-top"><div><p className="eyebrow">{t('BUILT WITH INTENTION')}</p><h2>{t('Clarity at every step')}</h2></div></div><div className="principle"><span className="principle-icon"><ShieldCheck size={20} /></span><div><strong>{t('Curated, not crowded')}</strong><p>{t('Each public preview is deliberately selected and approved.')}</p></div></div><div className="principle"><span className="principle-icon"><Search size={20} /></span><div><strong>{t('Made to explore')}</strong><p>{t('Discover visual work by project, story, and format.')}</p></div></div><div className="principle"><span className="principle-icon"><LockKeyhole size={20} /></span><div><strong>{t('Access is considered')}</strong><p>{t('Original downloads require their own approval.')}</p></div></div><button className="text-link" onClick={() => navigate('/about')}>{t('About the studio')} <ArrowUpRight size={16} /></button></Card></div>
  </>
}

function ShowcaseRow({ showcase, navigate }: { showcase: PublicShowcase; navigate: (path: Route) => void }) {
  const { t } = useLanguage()
  return <a className="asset-row showcase-row" href={showcaseUrl(showcase)} onClick={event => { if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return; event.preventDefault(); navigate(showcaseUrl(showcase)) }}><span className="asset-row-icon"><Layers size={18} /></span><div><strong>{showcase.title}</strong><small>{projectName(showcase.projectId)} · {showcase.category}</small></div><Badge tone={showcase.publication === 'downloadable' ? 'success' : 'accent'}>{showcase.publication === 'downloadable' ? t('Downloadable') : t('Showcase')}</Badge></a>
}

function Explore({ catalog, navigate }: { catalog: PublicCatalog; navigate: (path: Route) => void }) {
  const { t } = useLanguage()
  return <><PageHeader eyebrow={t('LIBRARY / 01')} title={t('Explore assets')} description={t('Discover creative work through its story, project, and approved previews.')} aside={<Badge tone="accent">{t('{count} showcased', { count: catalog.showcases.length })}</Badge>} /><AssetExplorer showcases={catalog.showcases} navigate={item => navigate(showcaseUrl(item))} /></>
}

function Collections({ catalog, navigate }: { catalog: PublicCatalog; navigate: (path: Route) => void }) {
  const { t } = useLanguage()
  const collections = projectCollections(catalog.showcases)
  return <><PageHeader eyebrow={t('LIBRARY / 02')} title={t('Collections')} description={t('Creative work, gathered by project.')} aside={<Badge tone="accent">{t('{count} published', { count: collections.length })}</Badge>} /><Card className="page-panel">{collections.length === 0 ? <EmptyState title={t('No public collections yet')} description={t('Projects appear here when their showcase previews are approved. Draft and private projects stay out of view.')} /> : <div className="collection-grid">{collections.map(collection => <a className="ui-card collection-card collection-link" key={collection.id} href={`/collections/${collection.id}`} onClick={event => { if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return; event.preventDefault(); navigate(`/collections/${collection.id}`) }}><AssetPreview media={collection.preview} /><div className="collection-card-body"><p className="eyebrow">{t('PROJECT COLLECTION')}</p><h2>{collection.name}</h2><p>{t(collection.entries.length === 1 ? '{count} public showcase' : '{count} public showcases', { count: collection.entries.length })}</p><div className="collection-facets"><span>{t('Categories:')} {collection.categories.join(', ')}</span><span>{t('Formats:')} {collection.formats.join(', ')}</span></div></div></a>)}</div>}</Card></>
}

function CollectionDetail({ catalog, projectId, navigate }: { catalog: PublicCatalog; projectId: string; navigate: (path: Route) => void }) {
  const { t } = useLanguage()
  const collection = projectCollections(catalog.showcases).find(item => item.id === projectId)
  if (!collection) return <Card className="page-panel"><EmptyState title={t('Collection not found')} description={t('This project has no public showcases.')} action={<Button onClick={() => navigate('/collections')}>{t('All collections')} <ArrowRight size={16} /></Button>} /></Card>
  return <><button className="text-link collection-back" onClick={() => navigate('/collections')}>← {t('All collections')}</button><PageHeader eyebrow={t('PROJECT COLLECTION')} title={collection.name} description={`${t(collection.entries.length === 1 ? '{count} public showcase' : '{count} public showcases', { count: collection.entries.length })} · ${collection.categories.join(', ')} · ${collection.formats.join(', ')}`} /><AssetExplorer showcases={catalog.showcases} lockedProject={projectId} navigate={item => navigate(showcaseUrl(item))} /></>
}

function Health({ catalog }: { catalog: PublicCatalog }) {
  const { t } = useLanguage()
  return <><PageHeader eyebrow={t('OPERATIONS / 01')} title={t('Asset Health')} description={t('A public view of the checks that keep this space clear and trustworthy.')} /><div className="info-grid"><Card className="info-card"><span className="info-icon success"><Check size={21} /></span><p className="eyebrow">{t('PUBLIC CATALOG')}</p><h2>{t('Catalog loaded')}</h2><p>{t(catalog.showcases.length === 1 ? 'The public catalog contains {count} approved showcase.' : 'The public catalog contains {count} approved showcases.', { count: catalog.showcases.length })}</p></Card><Card className="info-card"><span className="info-icon"><ShieldCheck size={21} /></span><p className="eyebrow">{t('PUBLICATION')}</p><h2>{t('Explicit by design')}</h2><p>{t('Public previews and downloadable files require separate approval.')}</p></Card><Card className="info-card"><span className="info-icon"><LockKeyhole size={21} /></span><p className="eyebrow">{t('PRIVATE WORK')}</p><h2>{t('Kept behind the boundary')}</h2><p>{t('Internal validation details and unapproved sources and review evidence stay private.')}</p></Card></div><Card className="quiet-panel"><CircleHelp size={21} /><div><strong>{t('Looking for detailed validation?')}</strong><p>{t('Technical findings are reviewed within the private repository. This public page reports only the published surface.')}</p></div></Card></>
}

function About({ catalog }: { catalog: PublicCatalog }) {
  const { t } = useLanguage()
  return <><PageHeader eyebrow={t('THE STUDIO / ABOUT')} title={t('A home for considered assets')} description={t('Asset Studio brings approved FM Work visuals into one calm, useful space for people and projects.')} /><div className="about-lead"><p>{t('Creative work moves through many stages. This studio shows the part that is ready to be shared: approved previews with clear context and a reliable path back to their project.')}</p><Badge tone="accent">{t('Catalog v{version}', { version: catalog.schemaVersion })}</Badge></div><div className="info-grid about-grid"><Card className="info-card"><span className="step-number">01</span><h2>{t('Create')}</h2><p>{t('Artwork is developed in project workspaces, with sources, candidates, and review material kept in their appropriate places.')}</p></Card><Card className="info-card"><span className="step-number">02</span><h2>{t('Review')}</h2><p>{t('Files are checked for format, provenance, rights, and suitability before any publication decision.')}</p></Card><Card className="info-card"><span className="step-number">03</span><h2>{t('Showcase')}</h2><p>{t('Selected preview media can tell the story of an asset. Original downloads require separate approval.')}</p></Card></div><Card className="about-note"><div className="about-note-icon"><LockKeyhole size={25} /></div><div><p className="eyebrow">{t('A DELIBERATE BOUNDARY')}</p><h2>{t('The studio grows through approval.')}</h2><p>{t('There are currently {count} public showcases. New work appears only after its previews and rights are resolved.', { count: catalog.showcases.length })}</p></div></Card></>
}

export default function App() {
  const { t, language } = useLanguage()
  const { route, navigate } = useRoute()
  const { theme, toggleTheme } = useTheme()
  const { state, retry } = usePublicCatalog()
  const [menuOpen, setMenuOpen] = useState(false)
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setMenuOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  useEffect(() => {
    const title = route?.startsWith('/collections/') ? projectName(route.slice('/collections/'.length)) : route?.startsWith('/assets/') && state.status === 'ready' ? state.catalog.showcases.find(item => showcaseUrl(item) === route)?.title || 'Showcase' : nav.find(item => item.path === route)?.label ?? 'Page not found'
    document.title = `${t(title)} — Asset Studio`
    document.querySelector('meta[name="description"]')?.setAttribute('content', t('A considered space to explore published FM Work assets.'))
  }, [route, state, language])
  return <><a className="skip-link" href="#main-content">{t('Skip to content')}</a><div className="app-shell"><Sidebar route={route} navigate={navigate} /><div className="main-shell"><AppHeader route={route} theme={theme} toggleTheme={toggleTheme} menuOpen={menuOpen} setMenuOpen={setMenuOpen} catalogStatus={state.status} />{menuOpen && <nav id="mobile-navigation" className="mobile-navigation" aria-label={t('Mobile navigation')}>{nav.map(item => <NavItem key={item.path} item={item} active={route === item.path || (item.path === '/collections' && Boolean(route?.startsWith('/collections/'))) || (item.path === '/explore' && Boolean(route?.startsWith('/assets/')))} navigate={navigate} close={() => setMenuOpen(false)} />)}<ExternalNavItem href={SUPPORT_URL} label="Support" icon={CircleHelp} close={() => setMenuOpen(false)} /><ExternalNavItem href={GATEWAY_URL} label="More projects" icon={Layers} close={() => setMenuOpen(false)} /></nav>}<main id="main-content" tabIndex={-1} className="main-content"><div className="content-container">{route === null ? <Card className="page-panel"><EmptyState title={t('Page not found')} description={t('This page is not part of Asset Studio.')} action={<Button onClick={() => navigate('/')}>{t('Back to overview')} <ArrowRight size={16} /></Button>} /></Card> : state.status === 'loading' ? <LoadingState /> : state.status === 'error' ? <ErrorState message={state.message} retry={retry} /> : route === '/' ? <Overview catalog={state.catalog} navigate={navigate} /> : route === '/explore' ? <Explore catalog={state.catalog} navigate={navigate} /> : route === '/collections' ? <Collections catalog={state.catalog} navigate={navigate} /> : route.startsWith('/collections/') ? <CollectionDetail catalog={state.catalog} projectId={route.slice('/collections/'.length)} navigate={navigate} /> : route.startsWith('/assets/') ? <ShowcaseDetail catalog={state.catalog} showcase={state.catalog.showcases.find(item => showcaseUrl(item) === route)} navigate={navigate} /> : route === '/health' ? <Health catalog={state.catalog} /> : <About catalog={state.catalog} />}</div></main><footer className="app-footer"><span>© {new Date().getFullYear()} FM Work</span><span>{t('Thoughtfully organized, intentionally published.')}</span></footer></div></div></>
}
