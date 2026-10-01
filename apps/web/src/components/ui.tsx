import type { ButtonHTMLAttributes, HTMLAttributes, InputHTMLAttributes, TextareaHTMLAttributes } from 'react'

export function Button({ className = '', variant = 'primary', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' }) {
  return <button className={`button button-${variant} ${className}`.trim()} {...props} />
}

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`field-input ${className}`.trim()} {...props} />
}

export function TextArea({ className = '', ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`field-input ${className}`.trim()} {...props} />
}

export function Select({ className = '', children, ...props }: HTMLAttributes<HTMLSelectElement> & { children: React.ReactNode; value?: string; onChange?: (event: React.ChangeEvent<HTMLSelectElement>) => void }) {
  return (
    <select className={`field-input ${className}`.trim()} {...props}>
      {children}
    </select>
  )
}

export function Card({ children, className = '' }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`card ${className}`.trim()}>{children}</div>
}

export function Tag({ children, active = false }: { children: React.ReactNode; active?: boolean }) {
  return <button type="button" className={`tag ${active ? 'tag-active' : ''}`} aria-pressed={active}>{children}</button>
}

export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <header className="page-header">
      <p className="eyebrow">TravelMate</p>
      <h1>{title}</h1>
      {description ? <p className="muted">{description}</p> : null}
    </header>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return <div className="app-shell">{children}</div>
}
