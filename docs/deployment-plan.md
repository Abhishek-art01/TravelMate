# TravelMate Deployment Plan

Based on the current architecture (FastAPI backend, Vite/React frontends, Supabase Postgres/Auth, and Cloudflare R2), here is the recommended production deployment strategy.

## 1. Infrastructure Overview

| Component | Current Local Setup | Recommended Production Host | Why? |
| :--- | :--- | :--- | :--- |
| **Database** | Supabase (Remote) | **Supabase** (Already configured) | PostgreSQL + PostGIS is fully managed by Supabase. |
| **Authentication** | Supabase (Remote) | **Supabase** | Ready to go. Just need to update redirect URLs for production. |
| **Media Storage** | Cloudflare R2 (Remote)| **Cloudflare R2** | Zero egress fees, already configured. |
| **Backend API** | Docker (FastAPI) | **Render** or **Fly.io** | Easy Dockerfile deployments, native HTTPS, automatic CI/CD from GitHub, and scale-to-zero capabilities. |
| **Frontend Web** | Vite SPA (pnpm) | **Vercel** or **Cloudflare Pages** | Best-in-class CDN, automatic deployments, easy custom domains, and free tier. |
| **Admin Web** | Vite SPA (pnpm) | **Vercel** or **Cloudflare Pages** | Same as above. Can be protected by Vercel Authentication or Supabase RBAC. |
| **Redis Cache** | Docker (Local) | **Upstash** | Serverless Redis. Generous free tier, no maintenance, connects easily via `REDIS_URL`. |

---

## 2. Step-by-Step Deployment Strategy

### Phase 1: Database & Third-Party Services
1. **Redis**: Create a free Serverless Redis database on [Upstash](https://upstash.com). Copy the `REDIS_URL` for the backend.
2. **Supabase Auth**: Go to Supabase Dashboard -> Authentication -> URL Configuration. Add your future production URLs (e.g., `https://travelmate.app`) to the **Site URL** and **Redirect URLs**.

### Phase 2: Deploying the Backend API (Render)
1. Create a new "Web Service" on [Render.com](https://render.com).
2. Connect your GitHub repository.
3. Configure the service:
   * **Root Directory**: `services/api`
   * **Environment**: `Docker`
   * **Instance Type**: Starter ($7/mo) or Free tier.
4. Add all required Environment Variables (copy from your `.env`), making sure to update:
   * `APP_ENVIRONMENT=production`
   * `REDIS_URL=<upstash_redis_url>`
5. Deploy. Render will build the Dockerfile and expose an `https://...onrender.com` URL.

### Phase 3: Deploying the Frontends (Vercel)
1. Go to [Vercel](https://vercel.com) and import the GitHub repository.
2. **For the User Web App**:
   * **Framework Preset**: Vite
   * **Root Directory**: `apps/web`
   * **Environment Variables**: Add `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL` (pointing to the new Render backend URL).
3. **For the Admin Web App**:
   * Repeat the same process, but set the **Root Directory** to `apps/admin-web`.
4. Deploy both. Vercel will give you production `.vercel.app` URLs.

### Phase 4: Final Configuration
1. **CORS**: Update the FastAPI backend environment variables to allow CORS requests from your new Vercel production frontend URLs.
2. **Custom Domains**: (Optional) Add your custom domain to Vercel for the frontends, and Render for the backend API.

---

## 3. Alternative: Deploy Everything to a Single VPS (e.g., DigitalOcean / AWS EC2)
If you prefer to host everything on a single server to save costs or maintain full control, we can use **Docker Compose**.
1. Provision an Ubuntu server.
2. Install Docker and Nginx (or Traefik).
3. Use a modified `docker-compose.prod.yml` to run the Backend, Web, Admin, and Redis containers.
4. Set up Let's Encrypt for SSL.
*Pros: Cheaper if traffic is high. Cons: More manual maintenance and downtime during deployments.*
