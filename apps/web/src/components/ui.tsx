import { useState, type ButtonHTMLAttributes, type HTMLAttributes, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react'

export function Button({ className = '', variant = 'primary', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' }) {
  return <button className={`button button-${variant} ${className}`.trim()} {...props} />
}

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`field-input ${className}`.trim()} {...props} />
}

export function PasswordInput({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  const [showPassword, setShowPassword] = useState(false)
  return (
    <div className="password-input-wrap">
      <Input
        type={showPassword ? 'text' : 'password'}
        className={`password-input ${className}`.trim()}
        {...props}
      />
      <button
        type="button"
        className="password-toggle-btn"
        onClick={() => setShowPassword((prev) => !prev)}
        aria-label={showPassword ? 'Hide password' : 'Show password'}
        title={showPassword ? 'Hide password' : 'Show password'}
      >
        {showPassword ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
            <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
            <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
            <line x1="2" y1="2" x2="22" y2="22" />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
      </button>
    </div>
  )
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
