import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="landing-layout">
      {/* HEADER */}
      <header className="landing-header">
        <div className="landing-logo">
          <img src="/logo-horizontal.png" alt="TravelMate" className="landing-logo-img" onError={(e) => { e.currentTarget.src = '/logo.png'; }} />
        </div>
        <div className="landing-nav">
          <Link to="/login" className="button button-secondary" style={{ padding: '0 24px', borderRadius: '30px', fontWeight: '600' }}>Log In</Link>
          <Link to="/signup" className="button button-primary" style={{ padding: '0 24px', borderRadius: '30px', fontWeight: '600', background: 'var(--coral)', color: 'white' }}>Sign Up</Link>
        </div>
      </header>

      <main className="landing-main">
        {/* HERO SECTION */}
        <section className="landing-hero-advanced">
          <div className="hero-content">
            <div className="hero-badge">Spark a connection worldwide</div>
            <h1>Don't explore the world <span className="highlight-text">alone</span>.</h1>
            <p className="hero-subtitle">
              The premier dating and companion app for travelers. Match with people heading to your dream destinations, build an itinerary together, and turn a solo trip into the romance of a lifetime.
            </p>
            <div className="hero-actions">
              <Link to="/signup" className="button button-primary hero-cta-large">Start Matching</Link>
              <p className="hero-subtext">Free to join. Available worldwide.</p>
            </div>
          </div>
          
          <div className="hero-mockup-wrapper">
            <div className="mockup-card back-card"></div>
            <div className="mockup-card front-card">
              <div className="mockup-img" style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1539635278303-d4002c07eae3?auto=format&fit=crop&q=80&w=800")' }}>
                <div className="mockup-badge">98% Match</div>
              </div>
              <div className="mockup-info">
                <div className="mockup-name">Elena, 27 <span>✈️ Heading to Tokyo</span></div>
                <div className="mockup-bio">Looking for someone to explore hidden sushi spots and neon-lit streets.</div>
                <div className="mockup-actions">
                  <div className="mockup-btn pass">✕</div>
                  <div className="mockup-btn like">♥</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="landing-section steps-section">
          <div className="section-header">
            <h2>How TravelMate Works</h2>
            <p>Your journey from single traveler to dynamic duo in three simple steps.</p>
          </div>
          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number">01</div>
              <h3>Set Your Destination</h3>
              <p>Add your upcoming trips, bucket-list destinations, and your travel style to your profile.</p>
            </div>
            <div className="step-card">
              <div className="step-number">02</div>
              <h3>Find Your Match</h3>
              <p>Our algorithm connects you with singles traveling to the exact same places at the same time.</p>
            </div>
            <div className="step-card">
              <div className="step-number">03</div>
              <h3>Plan Together</h3>
              <p>Chat securely, share our built-in collaborative itineraries, and meet up anywhere in the world.</p>
            </div>
          </div>
        </section>

        {/* FEATURES GRID */}
        <section className="landing-section features-advanced">
          <div className="section-header">
            <h2>Everything you need for a perfect trip.</h2>
          </div>
          <div className="features-bento">
            <div className="bento-box feature-verified">
              <div className="feature-icon">🛡️</div>
              <h3>Verified Travelers Only</h3>
              <p>We use government ID verification and liveness checks. Every person you talk to is real and verified for your safety abroad.</p>
            </div>
            <div className="bento-box feature-itinerary">
              <div className="feature-icon">🗺️</div>
              <h3>Collaborative Itineraries</h3>
              <p>Once you match, easily drop flights, hotels, and dinner reservations into a shared trip board.</p>
            </div>
            <div className="bento-box feature-vibe">
              <div className="feature-icon">✨</div>
              <h3>Vibe Checking</h3>
              <p>Filter matches by travel style: luxury resorts, rugged backpacking, foodie tours, or museum hopping.</p>
            </div>
          </div>
        </section>

        {/* TESTIMONIALS */}
        <section className="landing-section testimonials-section">
          <div className="section-header">
            <h2>Connections made everywhere.</h2>
          </div>
          <div className="testimonials-grid">
            <div className="testimonial-card">
              <p className="quote">"I was planning a solo trip to Bali, but I matched with Sarah two months before my flight. We planned the whole thing together on the app. We're engaged now!"</p>
              <div className="testimonial-author">
                <div className="author-avatar" style={{background: 'var(--coral)'}}>J</div>
                <div>
                  <strong>James & Sarah</strong>
                  <span>Matched for Bali, Indonesia</span>
                </div>
              </div>
            </div>
            <div className="testimonial-card">
              <p className="quote">"Finding someone who actually wants to wake up at 5 AM to hike Patagonia was impossible until TravelMate. The 'Travel Style' filter changed my life."</p>
              <div className="testimonial-author">
                <div className="author-avatar" style={{background: 'var(--blue)'}}>M</div>
                <div>
                  <strong>Maria</strong>
                  <span>Matched for Patagonia, Chile</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* BOTTOM CTA */}
        <section className="landing-bottom-cta">
          <h2>Ready for your next adventure?</h2>
          <p>Join thousands of travelers finding romance on the road.</p>
          <Link to="/signup" className="button button-primary cta-massive">Create Your Free Account</Link>
        </section>
      </main>

      <footer className="landing-footer-advanced">
        <div className="footer-content">
          <div className="footer-brand">
            <div className="landing-logo">
              <img src="/logo-horizontal.png" alt="TravelMate" className="landing-logo-img" onError={(e) => { e.currentTarget.src = '/logo.png'; }} />
            </div>
            <p>The #1 dating app for world travelers.</p>
          </div>
          <div className="footer-links">
            <div className="link-column">
              <h4>Company</h4>
              <a href="#">About Us</a>
              <a href="#">Careers</a>
              <a href="#">Press</a>
            </div>
            <div className="link-column">
              <h4>Legal</h4>
              <a href="/privacy">Privacy Policy</a>
              <a href="#">Terms of Service</a>
              <a href="#">Cookie Policy</a>
            </div>
            <div className="link-column">
              <h4>Safety</h4>
              <a href="#">Community Guidelines</a>
              <a href="#">Safety Tips</a>
              <a href="#">Report an Issue</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} TravelMate. Designed for adventurers everywhere.</p>
        </div>
      </footer>
    </div>
  )
}
