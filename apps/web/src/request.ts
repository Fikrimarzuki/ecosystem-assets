import type { PublicShowcase } from './catalog'

const configuredEmail = (import.meta.env.VITE_PUBLIC_CONTACT_EMAIL || '').trim()
export const publicContactEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(configuredEmail) && configuredEmail.length <= 254 ? configuredEmail : null

export function requestAssetHref(showcase: PublicShowcase, email = publicContactEmail): string | null {
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return null
  const subject = `Asset request: ${showcase.title}`
  const body = `Hello,\n\nI would like to request access to the public showcase "${showcase.title}" (${showcase.id}).\n\nIntended use:\n\nThank you.`
  return `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
}
