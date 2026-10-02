# Changelog

## 1.0.0 (2026-10-02)


### Features

* add logo and favicon assets, update web and admin branding, and clean gitignore ([1999d54](https://github.com/Abhishek-art01/TravelMate/commit/1999d5476787577a1b3f59dbcd1695acd929804e))
* **api:** integrate Sentry error tracking ([fe9dfce](https://github.com/Abhishek-art01/TravelMate/commit/fe9dfce40383d870bd9ab94ac56f20f89e374197))
* **auth:** add show/hide password toggle feature to web and admin login ([55a6f4a](https://github.com/Abhishek-art01/TravelMate/commit/55a6f4ad83fe22484e92c70d31961a1fdf98e18b))
* **scripts:** add Bitwarden (bw) and dotenvx to setup-cli-ecosystem.sh ([9823505](https://github.com/Abhishek-art01/TravelMate/commit/98235056eb27698be6a03bcdb8d6cb017b408208))
* **scripts:** add Ponytail plugin installer and fix dynamic workspace path in setup-cli-ecosystem.sh ([bbf3e80](https://github.com/Abhishek-art01/TravelMate/commit/bbf3e80088214c39333e99575cf8f4aa4e92442f))
* setup PWA to make the app installable on mobile ([cac7a32](https://github.com/Abhishek-art01/TravelMate/commit/cac7a325560abe61b6cb6e8a983b0dd866c41e81))


### Bug Fixes

* **api:** add sentry_dsn to settings schema ([6e92a53](https://github.com/Abhishek-art01/TravelMate/commit/6e92a536e5e6291ee0387015f1f0eadda4458fb6))
* **backend:** add Supabase PgBouncer pooler and ES256 JWKS key support ([affa34d](https://github.com/Abhishek-art01/TravelMate/commit/affa34d3eb81fbec322a5ed50ca3530b55bc3caf))
* **db:** remove local db containers in favor of remote Supabase/Atlas links, fix migration 4 ([68e49fb](https://github.com/Abhishek-art01/TravelMate/commit/68e49fb7e0b0bee095fdf13b7f23d51c8f69284c))
* **docker:** migrate dev compose to pnpm and fix container env path resolution ([d096294](https://github.com/Abhishek-art01/TravelMate/commit/d096294b926bd2089d4071691c36afb88eea4284))
