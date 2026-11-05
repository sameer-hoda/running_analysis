# EC2 access — mynextpr.com

Cheat sheet for SSH'ing into the live box, plus what broke on **2026-11-05** and how
it was fixed. Key details are public-IP specific; no secrets beyond the repo-local
key path.

## The live box

| Item | Value |
|---|---|
| Instance | `i-0e4bd0f8af171bada` (name `mynextpr`), t3.micro, ap-southeast-2 |
| Public IP | `3.107.159.134` — auto-assigned, **changes on stop/start** (survives reboot) |
| DNS | `mynextpr.com` + `www` A-records point to the public IP — update if the IP ever changes |
| VPC / Subnet | `vpc-01694646d4f588086` / `subnet-0b504353c8b44439e` (default NACL, allow-all) |
| Security group | `sg-00b3454745cacc5a8` (`launch-wizard-5`): 80, 443, 22 all `0.0.0.0/0` |

**The public IP on the box can rotate.** If SSH/HTTP stop working suddenly with an
IP mismatch, first check the instance's current IP in the AWS console and compare
against DNS.

## Connect

```sh
ssh -i v2/mynextpr_v2.pem -o BatchMode=yes ec2-user@3.107.159.134
```

The same `mynextpr_v2.pem` unlocks this instance too (v6 box created Aug 2026).

Or the repo's runner report:

```sh
MY_NEXTPR_SSH_KEY="$PWD/v2/mynextpr_v2.pem" \
MY_NEXTPR_SSH_HOST=ec2-user@3.107.159.134 bash deploy/runner-report.sh
```

**Backup path — no SSH at all:** AWS console → EC2 → instance → Connect →
**SSM Session Manager** (IAM role `instanceRole`, policy `AmazonSSMManagedInstanceCore`,
attached 2026-11-05). Works even when the OS firewall blocks 22.

## OS-level firewall (iptables)

The box runs its own iptables (loaded by **`iptables.service`**, kept in
`/etc/sysconfig/iptables` + `.save`). Only SSH is restricted to one source IP:

```sh
# Rule 4 in the INPUT chain — update the IP when the home IP drifts:
sudo iptables -L INPUT -n --line-numbers | head -9
sudo iptables -D INPUT 4                       # remove old allow rule
sudo iptables -I INPUT 4 -s <YOUR_IP> -p tcp -m tcp --dport 22 -j ACCEPT
sudo sh -c 'iptables-save > /etc/sysconfig/iptables'   # persist across reboot
sudo cp /etc/sysconfig/iptables /etc/sysconfig/iptables.save
```

Home ISP IP is dynamic (observed drift within `49.207.x.x` on 2026-11-05).
Rule order: ESTABLISHED, ICMP, DROP :3000 (v2 backend), ACCEPT :22 (home IP),
ACCEPT :80/:443, ACCEPT everything else → REJECT.

If you lock yourself out, fix the rule via SSM Session Manager (above).

## Services on the box (after 2026-11-05)

| Unit | What it is | Port |
|---|---|---|
| `nginx` | Site TLS front door, proxies everything to upstream | 80/443 → `127.0.0.1:8139` |
| `mynextpr-v6` | **v6 live site backend** (`python3.11 v6/server.py`, env `PORT=8139`), systemd-managed, restarts on crash + boot | 8139 |
| `mynextpr-backend` | Legacy v2-era FastAPI backend (uvicorn, `backend/main.py`) — not proxied by the site | 3000 (DROPped by iptables) |

## 2026-11-05 outage — what happened & fix

1. **SSH blocked:** OS iptables allowed 22 only from old IP `49.207.146.7`; current
   IP was `49.207.150.167` → every connection dropped (SG + NACL were fine).
   Reboot didn't clear it because the rule is **persisted in
   `/etc/sysconfig/iptables`**.
2. **Regained access** via SSM (created role `instanceRole` +
   `AmazonSSMManagedInstanceCore`), replaced the rule, re-saved the file.
3. **Site went 502 after the reboot:** the v6 app had been running as a *bare
   process* (`PORT=8139 python3 v6/server.py`) — killed by reboot, nothing to
   restart it. Fixed by creating the `mynextpr-v6.service` systemd unit
   (see above), `enable --now`, verified 200 on `https://mynextpr.com`.

Manual start (only if the unit is broken): `cd ~/mynextpr-v6 && PORT=8139 nohup python3.11 v6/server.py &`

## Quick health check

```sh
curl -o /dev/null -w "%{http_code}\n" https://mynextpr.com/            # 200
curl -o /dev/null -w "%{http_code}\n" https://mynextpr.com/api/status  # 200
MY_NEXTPR_SSH_KEY="$PWD/v2/mynextpr_v2.pem" \
MY_NEXTPR_SSH_HOST=ec2-user@3.107.159.134 bash deploy/runner-report.sh
```

255 notes on hardening (not done, on record): the pem sits inside the repo at
`v2/mynextpr_v2.pem` — consider moving it to `~/.ssh/` out of git; SG allows 22
from anywhere but the OS firewall narrows it to one IP; consider an Elastic IP to
stop the IP-rotates problem forever.
