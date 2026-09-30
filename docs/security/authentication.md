# Authentication and Supabase JWT verification

TravelMate verifies bearer tokens from Supabase before it grants access to protected endpoints.

## Verification flow

- The client sends `Authorization: Bearer <supabase_access_token>`.
- The FastAPI gateway reads the credential from the HTTP Authorization header.
- The JWT is checked for the required claims, key ID, issuer, audience, and expiry.
- The public signing key is resolved from the configured Supabase JWKS endpoint.
- A cached key is reused when available; a refresh occurs when the token `kid` is not present in the local cache.
- Verification fails closed: no token is accepted when the issuer, audience, JWKS, or signature cannot be validated.

## Configuration

The backend expects these environment values to be set in the runtime environment:

- `SUPABASE_URL`
- `SUPABASE_JWT_ISSUER`
- `SUPABASE_JWT_AUDIENCE`
- `SUPABASE_JWKS_URL`

The service does not pin a Supabase JWT secret in source code and never trusts a client-supplied role or user ID without signature verification.

## Security decisions

- JWT verification is signature-based and uses RS256/JWKS public keys.
- The token is rejected when the issuer or audience mismatches the configured environment values.
- Unknown key IDs trigger JWKS refresh and a safe failure if the signing key is still unavailable.
- Session state is server-side controlled via revocation and account status logic rather than relying only on the JWT as a long-lived trust assertion.
