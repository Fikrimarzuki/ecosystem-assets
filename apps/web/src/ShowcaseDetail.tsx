import { useEffect, useState, type MouseEvent } from 'react'
import { ArrowLeft, ArrowUpRight, Download, Mail, ShieldCheck } from 'lucide-react'
import { AssetPreview } from './AssetExplorer'
import type { PublicCatalog, PublicShowcase } from './catalog'
import { Badge, Button, Card, EmptyState, PageHeader } from './components'
import { previewFormats, projectName, showcaseUrl } from './explorer'
import { requestAssetHref } from './request'
import { useLanguage } from './i18n'

function formatBytes(bytes: number) { return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(1)} MB` }

export function ShowcaseDetail({ catalog, showcase, navigate }: { catalog: PublicCatalog; showcase?: PublicShowcase; navigate: (path: string) => void }) {
  const { t } = useLanguage()
  const [selected, setSelected] = useState(0)
  useEffect(() => setSelected(0), [showcase?.id])
  if (!showcase) return <Card className="page-panel"><EmptyState title={t('Showcase not found')} description={t('This asset has not been approved for public display.')} action={<Button onClick={() => navigate('/explore')}>{t('Explore showcases')}</Button>} /></Card>
  const media = showcase.media[selected] || showcase.media[0]
  const request = requestAssetHref(showcase)
  const related = (showcase.relatedShowcaseIds || []).map(id => catalog.showcases.find(item => item.id === id)).filter((item): item is PublicShowcase => Boolean(item))
  const onRelated = (event: MouseEvent<HTMLAnchorElement>, item: PublicShowcase) => {
    if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
    event.preventDefault(); navigate(showcaseUrl(item))
  }
  return <>
    <button className="text-link collection-back" onClick={() => navigate('/explore')}><ArrowLeft size={15} /> {t('Explore')}</button>
    <PageHeader eyebrow={`${projectName(showcase.projectId).toUpperCase()} / ${showcase.category.toUpperCase()}`} title={showcase.title} description={showcase.description} aside={<Badge tone={showcase.publication === 'downloadable' ? 'success' : 'accent'}>{t(showcase.publication === 'downloadable' ? 'Downloadable' : 'Showcase only')}</Badge>} />
    <div className="detail-layout">
      <div className="detail-main"><Card className="detail-visual"><div className="detail-preview"><AssetPreview media={media} /></div>{media?.caption && <p className="detail-caption">{media.caption}</p>}</Card>
        {showcase.media.length > 1 && <div className="detail-thumbnails" role="group" aria-label={t('Gallery images')}>{showcase.media.map((item,index) => <button type="button" key={item.key} aria-label={`${t('Show image {number}', { number: index + 1 })}${item.caption ? `: ${item.caption}` : ''}`} aria-pressed={selected === index} onClick={() => setSelected(index)}><AssetPreview media={item} /><span>{item.caption || t('View {number}', { number: index + 1 })}</span></button>)}</div>}
        {related.length > 0 && <Card className="detail-related"><p className="eyebrow">{t('KEEP EXPLORING')}</p><h2>{t('Related work')}</h2><div>{related.map(item => <a key={item.id} href={showcaseUrl(item)} onClick={event => onRelated(event,item)}>{item.title}<ArrowUpRight size={15} /></a>)}</div></Card>}
      </div>
      <aside className="detail-aside"><Card className="detail-panel"><p className="eyebrow">{t('ABOUT THIS WORK')}</p><h2>{t('At a glance')}</h2><dl><div><dt>{t('Project')}</dt><dd>{projectName(showcase.projectId)}</dd></div><div><dt>{t('Category')}</dt><dd>{showcase.category}</dd></div><div><dt>{t('Preview formats')}</dt><dd>{previewFormats(showcase).join(', ') || t('None')}</dd></div><div><dt>{t('Gallery views')}</dt><dd>{showcase.media.length}</dd></div>{media?.dimensions && <div><dt>{t('Selected image')}</dt><dd>{media.dimensions.width} × {media.dimensions.height}</dd></div>}</dl></Card>
        <Card className="detail-panel detail-access"><span className="detail-access-icon"><ShieldCheck size={21} /></span><p className="eyebrow">{t('ACCESS')}</p><h2>{t(showcase.publication === 'downloadable' ? 'Approved downloads' : 'Request this asset')}</h2>
          <p>{t('Requests are reviewed individually. Sending a request does not guarantee access or permission to reuse this work.')}</p>
          {showcase.publication === 'downloadable' && <div className="detail-downloads">{showcase.downloads.map(file => <a key={file.key} href={file.url} download={`${showcase.slug}-${file.key}.${file.format}`}><Download size={16} /><span>{file.label || file.format.toUpperCase()}</span><small>{formatBytes(file.bytes)}</small></a>)}</div>}
          {request ? <a className="ui-button ui-button-primary detail-request" href={request}><Mail size={17} /> {t('Request Asset')}</a> : <><button className="ui-button ui-button-secondary detail-request" type="button" disabled>{t('Request Asset')}</button><small className="detail-contact-pending">{t('Public contact address is being configured.')}</small></>}
        </Card>
      </aside>
    </div>
  </>
}
