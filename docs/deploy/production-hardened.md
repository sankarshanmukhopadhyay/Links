# Production hardened profile (guidance)

## TLS & ingress
Links should be deployed **behind a TLS terminator** (e.g., Nginx/Envoy/API Gateway).
Run the Links process on loopback or a private network interface.

## Auth
- Use bearer tokens for management endpoints.
- Consider mTLS or gateway-level auth for stronger posture.

## Rate limiting
- The built-in limiter is a safety net.
- Enforce real rate limiting at the gateway.

## Storage
- Filesystem backend is simplest.
- Optional SQLite backend is planned; migrate if you need strong concurrency and atomic apply semantics.

## Observability
- Export audit logs periodically (`/audit/export` or `links audit export`)
- Ship logs to your SIEM.
