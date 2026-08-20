# Trade Watch

Watches a stock/ETF list for moving-average crossovers and RSI signals,
opens a GitHub Issue when one triggers (that's your approval screen), and
texts you a heads-up via your carrier's free email-to-SMS gateway.

**This tool does not trade for you and does not give investment advice.**
It flags when rules you defined in `config.yaml` are met, so you can decide
what to do and place the trade yourself.

## What you'll need

- A GitHub account (free) and a **private** repo for this code.
- An email account you can send from via SMTP with an "app password"
  (Gmail works well — see below). Free.
- Your phone number, for the carrier gateway. Free.

## Setup

### 1. Push this code to a new private GitHub repo

```bash
cd trade-watch
git init
git add .
git commit -m "Initial setup"
gh repo create trade-watch --private --source=. --push
# (or create the repo on github.com and `git remote add origin ...` + push)
```

### 2. Edit `config.yaml`

Set your watchlist and adjust thresholds if you want. Defaults:
50/200-day SMA crossover, RSI(14) with 30/70 thresholds.

### 3. Set up an app password for sending email

If using Gmail:
1. Turn on 2-Step Verification on your Google account.
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Create an app password for "Mail" — you'll get a 16-character code.

### 4. Add repo secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**.
Add these:

| Secret name | Value |
|---|---|
| `SMTP_SERVER` | `smtp.gmail.com` (or your provider's SMTP server) |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | your full email address |
| `SMTP_PASS` | the app password from step 3 |
| `SMS_GATEWAY_ADDRESS` | your phone number `@vtext.com`, e.g. `5551234567@vtext.com` |

Note: `SMS_GATEWAY_ADDRESS` uses `vtext.com` because Xfinity Mobile runs on
Verizon's network. If texts stop arriving, try `@mypixmessages.com` instead —
some Xfinity Mobile users have reported one working better than the other,
and it can change over time (this is an unofficial, unsupported gateway).

You don't need to add `GITHUB_TOKEN` — Actions provides it automatically.

### 5. Enable the workflow

Go to the **Actions** tab in your repo, and enable workflows if prompted.
The check will run automatically on weekdays after market close. You can
also trigger it manually anytime from Actions → Daily Trade Watch → Run workflow.

## How approval works

When a signal triggers, the script opens a GitHub Issue with the ticker,
signal type, and the numbers behind it, and sends you a short text so you
know to check it. You review the issue, decide whether it's worth acting
on, and — if so — place the trade yourself in your brokerage. Close the
issue (or leave a comment) once you've reviewed it, just to keep things tidy.

## If the free SMS gateway isn't reliable for you

Carrier email-to-SMS gateways can be inconsistent, and Xfinity Mobile users
in particular have reported hit-or-miss delivery. If that happens, swap in
[ntfy.sh](https://ntfy.sh) (free, more reliable, push notification instead
of a literal text):

1. Install the ntfy app, subscribe to a private topic name you make up.
2. Add an `NTFY_TOPIC` secret with that name.
3. In `src/notify.py`, uncomment the `send_via_ntfy` function.
4. In `src/main.py`, swap the `send_sms_via_email(...)` call for `send_via_ntfy(...)`.

## Customizing the strategy

All the indicator math lives in `src/indicators.py`, and the decision logic
in `src/main.py`'s `check_ticker()`. To add a different rule (e.g. a simple
% price move), write a new `detect_...()` function in `indicators.py` and
call it from `check_ticker()`.
