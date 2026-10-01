import { useState, type FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi, type AdminDestination, type AdminDestinationCreate } from '../services/api/admin'

type ModalState =
  | { mode: 'closed' }
  | { mode: 'create' }
  | { mode: 'edit'; destination: AdminDestination }

export default function AdminDestinations() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [modalState, setModalState] = useState<ModalState>({ mode: 'closed' })
  const [actionError, setActionError] = useState<string | null>(null)

  const destinationsQuery = useQuery({
    queryKey: ['admin', 'destinations', searchQuery, categoryFilter, statusFilter],
    queryFn: ({ signal }) =>
      adminApi.listDestinations(
        {
          query: searchQuery.trim() || undefined,
          category: categoryFilter,
          status: statusFilter,
          limit: 50,
        },
        signal,
      ),
  })

  const createMutation = useMutation({
    mutationFn: (data: AdminDestinationCreate) => adminApi.createDestination(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'destinations'] })
      setModalState({ mode: 'closed' })
      setActionError(null)
    },
    onError: (err: Error) => {
      setActionError(err.message || 'Failed to create destination')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AdminDestinationCreate> }) =>
      adminApi.updateDestination(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'destinations'] })
      setModalState({ mode: 'closed' })
      setActionError(null)
    },
    onError: (err: Error) => {
      setActionError(err.message || 'Failed to update destination')
    },
  })

  return (
    <div className="module-view">
      <header className="module-header">
        <p className="eyebrow">CATALOG OPERATIONS</p>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1>Destination Catalog</h1>
            <p className="module-description">
              Manage authoritative travel destinations, aliases, geospatial coordinates, and publication status.
            </p>
          </div>
          <button
            type="button"
            className="button button-primary"
            onClick={() => {
              setActionError(null)
              setModalState({ mode: 'create' })
            }}
          >
            + Add Destination
          </button>
        </div>
      </header>

      <section className="filter-bar" aria-label="Destination Filters">
        <div className="filter-group">
          <label htmlFor="dest-search">Search:</label>
          <input
            id="dest-search"
            type="search"
            className="select-input"
            style={{ width: 180 }}
            placeholder="Name, city, country..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="category-filter">Category:</label>
          <select
            id="category-filter"
            className="select-input"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="all">All Categories</option>
            <option value="city">City</option>
            <option value="beach">Beach</option>
            <option value="mountain">Mountain</option>
            <option value="cultural">Cultural</option>
            <option value="adventure">Adventure</option>
            <option value="nature">Nature</option>
            <option value="general">General</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="status-filter">Status:</label>
          <select
            id="status-filter"
            className="select-input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        <span className="queue-count">
          Total: {destinationsQuery.data?.total ?? 0}
        </span>
      </section>

      {destinationsQuery.isLoading && (
        <div className="loading-state">
          <span className="spinner" />
          <p>Loading destinations catalog…</p>
        </div>
      )}

      {destinationsQuery.isError && (
        <div className="error-card" role="alert">
          <p><strong>Failed to load destinations:</strong> {destinationsQuery.error.message}</p>
          <button type="button" className="button button-secondary" onClick={() => void destinationsQuery.refetch()}>
            Retry
          </button>
        </div>
      )}

      {destinationsQuery.isSuccess && (
        <div className="table-responsive">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Destination</th>
                <th>Location</th>
                <th>Coordinates</th>
                <th>Category</th>
                <th>Aliases</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {destinationsQuery.data.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-cell">
                    No destinations match the selected filters.
                  </td>
                </tr>
              ) : (
                destinationsQuery.data.items.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <div className="traveller-cell">
                        <span className="traveller-name">{d.name}</span>
                        <span className="traveller-sub mono-id">/{d.slug}</span>
                      </div>
                    </td>
                    <td>
                      <div>
                        {d.city ? `${d.city}, ` : ''}{d.region}, {d.country} ({d.country_code})
                      </div>
                    </td>
                    <td>
                      <span className="mono-id">
                        {d.latitude.toFixed(4)}, {d.longitude.toFixed(4)}
                      </span>
                    </td>
                    <td>
                      <span className="type-badge">{d.category}</span>
                    </td>
                    <td>
                      {d.aliases && d.aliases.length > 0 ? (
                        <span style={{ fontSize: '0.74rem', color: 'var(--muted)' }}>
                          {d.aliases.join(', ')}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--muted)' }}>—</span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge status-${d.status}`}>{d.status}</span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="button button-small button-secondary"
                        onClick={() => {
                          setActionError(null)
                          setModalState({ mode: 'edit', destination: d })
                        }}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit Modal */}
      {modalState.mode !== 'closed' && (
        <div className="admin-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="admin-modal-card" style={{ maxWidth: 540 }}>
            <h2 id="modal-title">
              {modalState.mode === 'create' ? 'Add New Destination' : `Edit ${modalState.destination.name}`}
            </h2>
            <p>
              {modalState.mode === 'create'
                ? 'Register an authoritative destination for trip planning and discovery.'
                : 'Update destination metadata, aliases, coordinates, or publication status.'}
            </p>

            {actionError && (
              <div className="inline-error" style={{ marginBottom: 16 }}>
                <span>{actionError}</span>
              </div>
            )}

            <DestinationForm
              destination={modalState.mode === 'edit' ? modalState.destination : undefined}
              isSubmitting={createMutation.isPending || updateMutation.isPending}
              onCancel={() => setModalState({ mode: 'closed' })}
              onSubmit={(formData) => {
                if (modalState.mode === 'create') {
                  createMutation.mutate(formData as AdminDestinationCreate)
                } else {
                  updateMutation.mutate({ id: modalState.destination.id, data: formData })
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function DestinationForm({
  destination,
  isSubmitting,
  onCancel,
  onSubmit,
}: {
  destination?: AdminDestination
  isSubmitting: boolean
  onCancel: () => void
  onSubmit: (data: Partial<AdminDestinationCreate>) => void
}) {
  const [name, setName] = useState(destination?.name ?? '')
  const [slug, setSlug] = useState(destination?.slug ?? '')
  const [country, setCountry] = useState(destination?.country ?? '')
  const [countryCode, setCountryCode] = useState(destination?.country_code ?? '')
  const [region, setRegion] = useState(destination?.region ?? '')
  const [city, setCity] = useState(destination?.city ?? '')
  const [description, setDescription] = useState(destination?.description ?? '')
  const [latitude, setLatitude] = useState(destination?.latitude != null ? String(destination.latitude) : '')
  const [longitude, setLongitude] = useState(destination?.longitude != null ? String(destination.longitude) : '')
  const [timezone, setTimezone] = useState(destination?.timezone ?? 'UTC')
  const [category, setCategory] = useState(destination?.category ?? 'city')
  const [status, setStatus] = useState(destination?.status ?? 'active')
  const [aliasesStr, setAliasesStr] = useState(destination?.aliases ? destination.aliases.join(', ') : '')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const latNum = parseFloat(latitude)
    const lngNum = parseFloat(longitude)
    if (Number.isNaN(latNum) || Number.isNaN(lngNum)) {
      return
    }

    const aliases = aliasesStr
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)

    onSubmit({
      name,
      slug: slug || name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''),
      country,
      country_code: countryCode.toUpperCase(),
      region,
      city: city.trim() || null,
      description: description.trim() || null,
      latitude: latNum,
      longitude: lngNum,
      timezone: timezone || 'UTC',
      category,
      status,
      aliases,
    })
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Name *</label>
          <input
            type="text"
            required
            className="field-input"
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              if (!destination) {
                setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''))
              }
            }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Slug *</label>
          <input
            type="text"
            required
            className="field-input"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 10 }}>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Country *</label>
          <input
            type="text"
            required
            className="field-input"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Country Code (2-3) *</label>
          <input
            type="text"
            required
            maxLength={3}
            className="field-input"
            value={countryCode}
            onChange={(e) => setCountryCode(e.target.value)}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Region / State *</label>
          <input
            type="text"
            required
            className="field-input"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>City</label>
          <input
            type="text"
            className="field-input"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Latitude *</label>
          <input
            type="number"
            step="any"
            required
            min="-90"
            max="90"
            className="field-input"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Longitude *</label>
          <input
            type="number"
            step="any"
            required
            min="-180"
            max="180"
            className="field-input"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Category</label>
          <select className="field-input" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="city">City</option>
            <option value="beach">Beach</option>
            <option value="mountain">Mountain</option>
            <option value="cultural">Cultural</option>
            <option value="adventure">Adventure</option>
            <option value="nature">Nature</option>
            <option value="general">General</option>
          </select>
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Status</label>
          <select className="field-input" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Timezone</label>
          <input
            type="text"
            className="field-input"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Aliases (comma-separated)</label>
        <input
          type="text"
          className="field-input"
          placeholder="e.g. Bombay, Bambai"
          value={aliasesStr}
          onChange={(e) => setAliasesStr(e.target.value)}
        />
      </div>

      <div>
        <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ink)' }}>Description</label>
        <textarea
          rows={2}
          className="field-input"
          style={{ resize: 'vertical' }}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div className="admin-modal-actions">
        <button type="button" className="button button-secondary" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
        <button type="submit" className="button button-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : destination ? 'Update Destination' : 'Create Destination'}
        </button>
      </div>
    </form>
  )
}
