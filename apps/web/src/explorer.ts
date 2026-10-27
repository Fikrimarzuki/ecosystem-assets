import type { PublicShowcase } from './catalog'

export type Sort = 'name-asc' | 'name-desc' | 'size-asc' | 'size-desc'
export type View = 'grid' | 'list'
export interface ExplorerState { q: string; project: string; category: string; format: string; sort: Sort; view: View }
export const defaultExplorerState: ExplorerState = { q: '', project: '', category: '', format: '', sort: 'name-asc', view: 'grid' }
const sorts: Sort[] = ['name-asc', 'name-desc', 'size-asc', 'size-desc']

export function parseExplorerQuery(search: string): ExplorerState {
  const params = new URLSearchParams(search)
  const sort = params.get('sort') as Sort
  const view = params.get('view') as View
  return {
    q: (params.get('q') || '').slice(0, 200),
    project: params.get('project') || '',
    category: params.get('category') || '',
    format: params.get('format') || '',
    sort: sorts.includes(sort) ? sort : 'name-asc',
    view: view === 'list' ? 'list' : 'grid',
  }
}

export function serializeExplorerQuery(state: ExplorerState): string {
  const params = new URLSearchParams()
  for (const key of ['q', 'project', 'category', 'format'] as const) if (state[key]) params.set(key, state[key])
  if (state.sort !== 'name-asc') params.set('sort', state.sort)
  if (state.view !== 'grid') params.set('view', state.view)
  return params.toString()
}

export function projectName(id: string): string { return id.length <= 2 ? id.toUpperCase() : id.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[-_]+/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) }
export function showcaseUrl(showcase: PublicShowcase): string { return `/assets/${showcase.projectId}/${showcase.slug}` }
export function previewFormats(showcase: PublicShowcase): string[] { return [...new Set(showcase.media.map(item => item.format.toUpperCase()))].sort() }
export function showcaseSize(showcase: PublicShowcase): number { return showcase.media.reduce((sum, item) => sum + item.bytes, 0) }

export function selectShowcases(showcases: PublicShowcase[], state: ExplorerState, lockedProject?: string): PublicShowcase[] {
  const words = state.q.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean)
  return showcases.filter(showcase => {
    if ((lockedProject && showcase.projectId !== lockedProject) || (!lockedProject && state.project && showcase.projectId !== state.project) ||
      (state.category && showcase.category !== state.category) || (state.format && !showcase.media.some(item => item.format === state.format))) return false
    const haystack = [showcase.title, showcase.description, projectName(showcase.projectId), ...(showcase.tags || []), ...showcase.media.map(item => item.caption || '')].join(' ').toLocaleLowerCase()
    return words.every(word => haystack.includes(word))
  }).sort((a, b) => {
    const name = a.title.localeCompare(b.title) || a.id.localeCompare(b.id)
    if (state.sort === 'name-desc') return -name
    if (state.sort === 'size-asc') return showcaseSize(a) - showcaseSize(b) || name
    if (state.sort === 'size-desc') return showcaseSize(b) - showcaseSize(a) || name
    return name
  })
}

export function projectCollections(showcases: PublicShowcase[]) {
  const groups = new Map<string, PublicShowcase[]>()
  for (const showcase of showcases) groups.set(showcase.projectId, [...(groups.get(showcase.projectId) || []), showcase])
  return [...groups].sort(([a], [b]) => projectName(a).localeCompare(projectName(b))).map(([id, entries]) => ({
    id, name: projectName(id), entries,
    categories: [...new Set(entries.map(item => item.category))].sort(),
    formats: [...new Set(entries.flatMap(item => [...item.media,...item.downloads].map(file => file.format.toUpperCase())))].sort(),
    preview: entries.flatMap(item => item.media).find(file => ['png','svg','ico','jpg','jpeg','webp','gif','avif'].includes(file.format)),
  }))
}
