interface TravelMateMapProps {
  latitude: number
  longitude: number
  title?: string
  mode?: 'destination' | 'approximate' | 'exact'
  radiusKm?: number
  height?: number | string
}

export function TravelMateMap({
  latitude,
  longitude,
  title = 'Destination Location',
  mode = 'destination',
  radiusKm = 5,
  height = 220,
}: TravelMateMapProps) {
  const isApprox = mode === 'approximate'
  const latDisplay = isApprox ? `${latitude.toFixed(2)}°N` : `${latitude.toFixed(4)}°N`
  const lonDisplay = isApprox ? `${longitude.toFixed(2)}°E` : `${longitude.toFixed(4)}°E`

  return (
    <div
      className="travelmate-map-container"
      style={{ height }}
      role="region"
      aria-label={`Geographic map preview for ${title}`}
    >
      <svg
        className="travelmate-map-svg"
        viewBox="0 0 400 220"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
          </pattern>
          <radialGradient id="privacyGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--accent, #e5a93c)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="var(--accent, #e5a93c)" stopOpacity="0.0" />
          </radialGradient>
        </defs>

        {/* Map background grid */}
        <rect width="100%" height="100%" fill="#121820" />
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* Stylized topological contours */}
        <path
          d="M-20,160 Q80,110 180,150 T380,120 T440,180"
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="1.5"
        />
        <path
          d="M-20,90 Q90,50 200,90 T420,70"
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="1.5"
        />

        {/* Approximate privacy radius circle */}
        <circle cx="200" cy="110" r="45" fill="url(#privacyGlow)" />
        <circle
          cx="200"
          cy="110"
          r="45"
          fill="none"
          stroke="var(--accent, #e5a93c)"
          strokeWidth="1.5"
          strokeDasharray="4 3"
        />

        {/* Center pin / indicator */}
        <circle cx="200" cy="110" r="6" fill="var(--accent, #e5a93c)" />
        <circle cx="200" cy="110" r="2.5" fill="#121820" />
      </svg>

      <div className="travelmate-map-overlay">
        <div className="map-badge-group">
          <span className="map-badge">
            {isApprox ? `Approximate Zone (~${radiusKm}km)` : 'Destination Center'}
          </span>
          <span className="map-coords">
            {latDisplay}, {lonDisplay}
          </span>
        </div>
        <p className="map-privacy-note">
          {isApprox
            ? 'Privacy protected: Exact GPS coordinates are never exposed to other members.'
            : `Coordinates for ${title} provided for itinerary planning.`}
        </p>
      </div>
    </div>
  )
}
