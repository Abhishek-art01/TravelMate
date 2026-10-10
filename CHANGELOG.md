# Changelog

## 1.0.0 (2026-10-10)


### Features

* add logo and favicon assets, update web and admin branding, and clean gitignore ([67f7190](https://github.com/AbhishekPanthera/TravelMate/commit/67f71902892325a8ae3ee5110f4241eb57b2a783))
* add OTP email verification flow for signup ([bd04fff](https://github.com/AbhishekPanthera/TravelMate/commit/bd04fffb8e0d566305ac4d23420710a4409452da))
* add resend OTP button with 60s countdown ([f7e9fb8](https://github.com/AbhishekPanthera/TravelMate/commit/f7e9fb8e69710eb31d619490935313b94a5dbf77))
* **api:** integrate Sentry error tracking ([e591630](https://github.com/AbhishekPanthera/TravelMate/commit/e59163000d3a1498b38ee1eb669f85403433a8ef))
* **auth:** add show/hide password toggle feature to web and admin login ([d4c0a96](https://github.com/AbhishekPanthera/TravelMate/commit/d4c0a960a01bc104984c626e58e94caa266ae501))
* polish 10-step onboarding UI using native components ([fda27bd](https://github.com/AbhishekPanthera/TravelMate/commit/fda27bd2886dd6a5a02fcc8e7a7f493048b373d7))
* **scripts:** add Bitwarden (bw) and dotenvx to setup-cli-ecosystem.sh ([8d5fb9f](https://github.com/AbhishekPanthera/TravelMate/commit/8d5fb9fa13d816900664efb4c4ec19ab4ebfe481))
* **scripts:** add Ponytail plugin installer and fix dynamic workspace path in setup-cli-ecosystem.sh ([79e47a4](https://github.com/AbhishekPanthera/TravelMate/commit/79e47a451cbd3d9cd3b3c231ff0dc598f4c98509))
* setup PWA to make the app installable on mobile ([4792337](https://github.com/AbhishekPanthera/TravelMate/commit/4792337c4afd8e528caa4f986ec20112fd7a5de4))


### Bug Fixes

* **api:** add sentry_dsn to settings schema ([a3e130b](https://github.com/AbhishekPanthera/TravelMate/commit/a3e130baa0be67c7f481ff1a362cf9a9a6253377))
* **backend:** add Supabase PgBouncer pooler and ES256 JWKS key support ([f53dd4e](https://github.com/AbhishekPanthera/TravelMate/commit/f53dd4ed91f282db1e09612204f90130cd99b701))
* **db:** remove local db containers in favor of remote Supabase/Atlas links, fix migration 4 ([3fd9b3b](https://github.com/AbhishekPanthera/TravelMate/commit/3fd9b3bf09cd669b57fe4bcd0c1001bca84b2d57))
* **docker:** migrate dev compose to pnpm and fix container env path resolution ([eba3171](https://github.com/AbhishekPanthera/TravelMate/commit/eba31711e4a42f92683a8d37d52f735f829d23a7))
