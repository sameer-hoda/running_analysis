# 5. Deploy and operations

Live host details, key location, and running processes live in a private ops file outside the repo (`mynextpr-ec2.private.md` in the owner's home directory) — never in the public tree.

## Stack

nginx on 80/443 (HTTPS via certbot) proxies `mynextpr.com` to the Python backend on `127.0.0.1:8139`. The old app's files are untouched for rollback.

## Redeploy (local → live)

1. `tar --exclude=__pycache__ --exclude=.tokens.json --exclude=.athletes --exclude=strava-config.js -czf /tmp/mynextpr-v6.tgz v6/`
2. `scp` the tarball to EC2 (key path in the EC2 doc).
3. Extract over `~/mynextpr-v6` (keeps remote `.env`, tokens, web config).
4. Restart the server; verify homepage 200 and `/api/status`.

## Notes

- Run with `python3.11` on the box (system `python3` is 3.9).
- The remote `.env` (client ID/secret, verify token, redirect URI) and `.athletes/` are never overwritten by deploys.
- Local backend (`python3 v6/server.py` → :8123) is for page tinkering only; OAuth must go through the live domain.
