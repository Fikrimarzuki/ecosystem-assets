import { useCallback, useEffect, useState } from 'react'

export interface PublicAsset {
  id: string
  projectId: string
  path: string
  role: 'export'
  category: string
  format: string
  bytes: number
  sha256: string
  publication: 'public'
  rightsStatus: 'verified'
  dimensions?: { width: number; height: number }
  url: string
  title?: string
  description?: string
  tags?: string[]
}

export interface PublicCollection {
  id: string
  projectId: string
  physicalAssetIds: string[]
}

export interface PublicCatalog {
  schemaVersion: 1
  assets: PublicAsset[]
  logicalAssets: PublicCollection[]
  showcases: PublicShowcase[]
}

export interface PublicMedia {
  key: string
  url: string
  format: string
  bytes: number
  sha256: string
  dimensions?: { width: number; height: number }
  caption?: string
  label?: string
}

export interface PublicShowcase {
  id: string
  projectId: string
  slug: string
  title: string
  description: string
  category: string
  publication: 'showcase' | 'downloadable'
  tags?: string[]
  logicalAssetId?: string
  relatedShowcaseIds?: string[]
  media: PublicMedia[]
  downloads: PublicMedia[]
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function safePath(path: string): boolean {
  return !path.startsWith('/') && !path.includes('\\') && !path.split('/').some(part => !part || part === '.' || part === '..')
}

export function parsePublicCatalog(value: unknown): PublicCatalog {
  if (!object(value) || value.schemaVersion !== 1 || !Array.isArray(value.assets) || !Array.isArray(value.logicalAssets)) {
    throw new Error('The public catalog has an unexpected structure.')
  }
  const ids = new Set<string>()
  for (const asset of value.assets) {
    if (!object(asset) || typeof asset.id !== 'string' || typeof asset.projectId !== 'string' || typeof asset.path !== 'string' ||
      !safePath(asset.path) || asset.id !== `file:${asset.path}` || asset.role !== 'export' ||
      typeof asset.category !== 'string' || typeof asset.format !== 'string' || typeof asset.bytes !== 'number' || asset.bytes < 0 ||
      typeof asset.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(asset.sha256) ||
      typeof asset.url !== 'string' || !/^\/published\/[a-f0-9]{64}\.[a-z0-9]+$/.test(asset.url) || !asset.url.endsWith(`.${asset.format}`) ||
      (asset.title !== undefined && (typeof asset.title !== 'string' || !asset.title.trim())) ||
      (asset.description !== undefined && (typeof asset.description !== 'string' || !asset.description.trim())) ||
      (asset.tags !== undefined && (!Array.isArray(asset.tags) || !asset.tags.every(tag => typeof tag === 'string'))) ||
      asset.publication !== 'public' || asset.rightsStatus !== 'verified' || ids.has(asset.id) ||
      'sourceMetadata' in asset || 'relatedAssetIds' in asset || 'logicalAssetIds' in asset) {
      throw new Error('The public catalog contains an invalid asset record.')
    }
    ids.add(asset.id)
  }
  for (const group of value.logicalAssets) {
    if (!object(group) || typeof group.id !== 'string' || typeof group.projectId !== 'string' || !Array.isArray(group.physicalAssetIds) ||
      !group.physicalAssetIds.every(id => typeof id === 'string' && ids.has(id)) || 'legacyId' in group || 'status' in group) {
      throw new Error('The public catalog contains an invalid collection.')
    }
  }
  const showcases: unknown[] = value.showcases === undefined ? (value.assets as PublicAsset[]).map((asset, index) => ({
    id:`${asset.projectId}/legacy-${index + 1}`,projectId:asset.projectId,slug:`legacy-${index + 1}`,
    title:asset.title || asset.path.split('/').at(-1) || 'Approved asset',description:asset.description || 'Approved asset export',
    category:asset.category,publication:'downloadable',tags:asset.tags,
    media:['png','svg','ico','jpg','jpeg','webp','gif','avif'].includes(asset.format) ? [{key:'preview',url:asset.url,format:asset.format,bytes:asset.bytes,sha256:asset.sha256,dimensions:asset.dimensions}] : [],
    downloads:[{key:'file',url:asset.url,format:asset.format,bytes:asset.bytes,sha256:asset.sha256,label:`${asset.format.toUpperCase()} file`}],
  })) : value.showcases as unknown[]
  if (!Array.isArray(showcases)) throw new Error('The public showcases have an unexpected structure.')
  const showcaseIds = new Set<string>()
  for (const showcase of showcases) {
    if (!object(showcase) || typeof showcase.projectId !== 'string' || !/^[A-Za-z0-9_-]+$/.test(showcase.projectId) ||
      typeof showcase.slug !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(showcase.slug) ||
      showcase.id !== `${showcase.projectId}/${showcase.slug}` || showcaseIds.has(showcase.id as string) ||
      !['title','description','category'].every(key => typeof showcase[key] === 'string' && (showcase[key] as string).trim()) ||
      !['showcase','downloadable'].includes(showcase.publication as string) || !Array.isArray(showcase.media) || !Array.isArray(showcase.downloads) ||
      (showcase.publication === 'showcase' && showcase.downloads.length > 0) ||
      (showcase.publication === 'downloadable' && showcase.downloads.length === 0) ||
      (showcase.tags !== undefined && (!Array.isArray(showcase.tags) || !showcase.tags.every(tag => typeof tag === 'string'))) ||
      (showcase.relatedShowcaseIds !== undefined && (!Array.isArray(showcase.relatedShowcaseIds) || !showcase.relatedShowcaseIds.every(id => typeof id === 'string'))) ||
      ['path','assetId','sourceMetadata','approvedBy','approvedOn'].some(key => key in showcase)) throw new Error('The public catalog contains an invalid showcase.')
    showcaseIds.add(showcase.id as string)
    for (const media of [...showcase.media,...showcase.downloads]) {
      if (!object(media) || typeof media.key !== 'string' || typeof media.format !== 'string' || typeof media.url !== 'string' ||
        !/^\/published\/[a-f0-9]{64}\.[a-z0-9]+$/.test(media.url) || !media.url.endsWith(`.${media.format}`) ||
        typeof media.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(media.sha256) ||
        typeof media.bytes !== 'number' || !Number.isSafeInteger(media.bytes) || media.bytes < 0 ||
        (media.caption !== undefined && typeof media.caption !== 'string') || (media.label !== undefined && typeof media.label !== 'string') ||
        ['path','assetId','sourceMetadata'].some(key => key in media)) throw new Error('The public catalog contains invalid showcase media.')
    }
  }
  for (const showcase of showcases as PublicShowcase[]) for (const id of showcase.relatedShowcaseIds || []) if (!showcaseIds.has(id)) throw new Error('The public catalog contains an unpublished related asset.')
  return { ...(value as unknown as Omit<PublicCatalog,'showcases'>), showcases:showcases as PublicShowcase[] }
}

type CatalogState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; catalog: PublicCatalog }

export function usePublicCatalog() {
  const [state, setState] = useState<CatalogState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setState({ status: 'loading' })
    fetch('/catalog.json', { signal: controller.signal, cache: 'no-store' })
      .then(async response => {
        if (!response.ok) throw new Error(`Public catalog unavailable (${response.status}).`)
        return parsePublicCatalog(await response.json())
      })
      .then(catalog => setState({ status: 'ready', catalog }))
      .catch(error => {
        if (!controller.signal.aborted) setState({ status: 'error', message: error instanceof Error ? error.message : 'Unable to load the public catalog.' })
      })
    return () => controller.abort()
  }, [attempt])

  const retry = useCallback(() => setAttempt(value => value + 1), [])
  return { state, retry }
}
