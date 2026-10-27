import { useEffect, useState } from 'react'

export type Theme = 'light' | 'dark'

function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem('asset-studio-theme')
    if (saved === 'light' || saved === 'dark') return saved
  } catch { /* storage may be unavailable */ }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(initialTheme)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#11151c' : '#f6f7f8')
    try { localStorage.setItem('asset-studio-theme', theme) } catch { /* storage may be unavailable */ }
  }, [theme])
  return { theme, toggleTheme: () => setTheme(value => value === 'light' ? 'dark' : 'light') }
}
