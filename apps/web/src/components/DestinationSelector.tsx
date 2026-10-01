import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { travelApi, type DestinationSummary } from '../services/api/travel'

interface DestinationSelectorProps {
  value: DestinationSummary | null
  onChange: (destination: DestinationSummary | null) => void
  disabled?: boolean
  label?: string
}

export function DestinationSelector({
  value,
  onChange,
  disabled = false,
  label = 'Search Destination',
}: DestinationSelectorProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<DestinationSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [error, setError] = useState<string | null>(null)

  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open || query.trim().length === 0) {
      return
    }

    const timer = setTimeout(async () => {
      setLoading(true)
      setError(null)
      try {
        const resp = await travelApi.searchDestinations(query.trim(), 8)
        setResults(resp.items)
        setSelectedIndex(-1)
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err.message || 'Failed to search destinations')
        }
      } finally {
        setLoading(false)
      }
    }, 250)

    return () => clearTimeout(timer)
  }, [query, open])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!open) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setOpen(true)
      }
      return
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (selectedIndex >= 0 && selectedIndex < results.length) {
        selectDestination(results[selectedIndex])
      }
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  function selectDestination(dest: DestinationSummary) {
    onChange(dest)
    setOpen(false)
    setQuery('')
    setSelectedIndex(-1)
  }

  function handleClear() {
    onChange(null)
    setQuery('')
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  return (
    <div className="destination-selector" ref={containerRef}>
      {label && <label className="field-label" htmlFor="destination-search-input">{label}</label>}

      {value ? (
        <div className="destination-selected-card" role="group" aria-label="Selected destination">
          <div className="destination-selected-info">
            <span className="destination-badge">{value.category}</span>
            <div className="destination-name-group">
              <strong className="destination-title">{value.name}</strong>
              <span className="destination-subtitle">
                {value.region}, {value.country}
              </span>
            </div>
          </div>
          {!disabled && (
            <button
              type="button"
              className="button button-text destination-clear-btn"
              onClick={handleClear}
              aria-label={`Change destination from ${value.name}`}
            >
              Change
            </button>
          )}
        </div>
      ) : (
        <div className="destination-input-wrapper">
          <input
            id="destination-search-input"
            ref={inputRef}
            type="text"
            className="field-input"
            placeholder="Type city or place (e.g. Goa, Mumbai, Paris)…"
            value={query}
            disabled={disabled}
            onChange={(e) => {
              setQuery(e.target.value)
              if (e.target.value.trim().length === 0) {
                setResults([])
              }
              setOpen(true)
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={handleKeyDown}
            aria-autocomplete="list"
            aria-expanded={open}
            aria-controls="destination-results-list"
          />
          {loading && <span className="destination-spinner" aria-hidden="true" />}

          {open && query.trim().length > 0 && (
            <ul
              id="destination-results-list"
              className="destination-dropdown"
              role="listbox"
            >
              {error && (
                <li className="destination-item-error" role="alert">
                  {error}
                </li>
              )}
              {!loading && !error && results.length === 0 && (
                <li className="destination-item-empty">
                  No destinations found for “{query}”. Try searching another city.
                </li>
              )}
              {results.map((dest, idx) => (
                <li
                  key={dest.id}
                  id={`dest-item-${dest.id}`}
                  role="option"
                  aria-selected={idx === selectedIndex}
                  className={`destination-item ${idx === selectedIndex ? 'active' : ''}`}
                  onClick={() => selectDestination(dest)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                >
                  <div className="destination-item-primary">
                    <span className="destination-name">{dest.name}</span>
                    <span className="destination-region">
                      {dest.region}, {dest.country}
                    </span>
                  </div>
                  <span className="destination-item-badge">{dest.category}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
