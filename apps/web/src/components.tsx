import type { ButtonHTMLAttributes, HTMLAttributes, InputHTMLAttributes, ReactNode } from 'react'
import { AlertCircle, ArrowRight, LoaderCircle, PackageOpen } from 'lucide-react'
import { useLanguage } from './i18n'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost'; children: ReactNode }
export function Button({ variant = 'primary', className = '', children, ...props }: ButtonProps) {
  return <button className={`ui-button ui-button-${variant} ${className}`} {...props}>{children}</button>
}

export function Card({ className = '', children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`ui-card ${className}`} {...props}>{children}</div>
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'accent' | 'success' }) {
  return <span className={`ui-badge ui-badge-${tone}`}>{children}</span>
}

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`ui-input ${className}`} {...props} />
}

export function PageHeader({ eyebrow, title, description, aside }: { eyebrow: string; title: string; description: string; aside?: ReactNode }) {
  return <div className="page-header">
    <div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>
    {aside && <div className="page-header-aside">{aside}</div>}
  </div>
}

export function EmptyState({ title, description, action, compact = false }: { title: string; description: string; action?: ReactNode; compact?: boolean }) {
  return <div className={`empty-state ${compact ? 'empty-state-compact' : ''}`}>
    <div className="empty-symbol" aria-hidden="true"><PackageOpen size={25} strokeWidth={1.7} /></div>
    <div><h2>{title}</h2><p>{description}</p>{action && <div className="empty-action">{action}</div>}</div>
  </div>
}

export function LoadingState() {
  const { t } = useLanguage()
  return <div className="state-panel" role="status" aria-live="polite"><LoaderCircle className="spin" size={23} /><div><h2>{t('Opening the studio')}</h2><p>{t('Loading the published catalog.')}</p></div></div>
}

export function ErrorState({ message, retry }: { message: string; retry: () => void }) {
  const { t } = useLanguage()
  const responseError = message.match(/^Public catalog unavailable \((\d+)\)\.$/)
  return <div className="state-panel error-panel" role="alert"><AlertCircle size={23} /><div><h2>{t('Catalog unavailable')}</h2><p>{responseError ? t('Public catalog unavailable ({status}).', { status: responseError[1] }) : t(message)}</p><Button variant="secondary" onClick={retry}>{t('Try again')} <ArrowRight size={15} /></Button></div></div>
}
