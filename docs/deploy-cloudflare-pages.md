# Deploying HELIOS to Cloudflare Pages

**Frontend:** Cloudflare Pages (Vue 3 SPA)
**Backend:** Railway (FastAPI — already live at `https://helios-backend-production.up.railway.app`)

Cloudflare Pages hosts the static frontend. The Railway backend stays — only the frontend host changes from Vercel to Cloudflare.

---

## Prerequisites

Push the current `dev` branch (or merge to `master`) to GitHub before starting.
Cloudflare Pages deploys directly from a GitHub repo.

```bash
cd helios-app
git push origin dev        # or: git push origin master
```

---

## Step 1 — Connect to Cloudflare Pages

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. Authorise Cloudflare to access your GitHub account if prompted
3. Select the repo: `antutroll27/helios-app`
4. Click **Begin setup**

---

## Step 2 — Configure the Build

| Setting | Value |
|---|---|
| **Production branch** | `master` |
| **Build command** | `npm install --legacy-peer-deps && npm run build` |
| **Build output directory** | `dist` |
| **Root directory** | *(leave blank — repo root)* |

> `--legacy-peer-deps` is required because `vite-plugin-pwa` does not yet declare Vite 8 as a supported peer.

---

## Step 3 — Add Environment Variables

Under **Environment variables** → **Production**, add all of the following:

| Variable | Value |
|---|---|
| `VITE_SUPABASE_URL` | `https://zciyjaaigefeearpzsip.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | *(your Supabase anon/publishable key)* |
| `VITE_BACKEND_URL` | `https://helios-backend-production.up.railway.app` |
| `VITE_AQICN_TOKEN` | *(your AQICN token from `.env`)* |
| `VITE_NASA_API_KEY` | *(your NASA API key from `.env`)* |

Then click **Save and Deploy**.

---

## Step 4 — Wait for the Build

Cloudflare will clone the repo, run the build command, and publish the `dist/` output.
Build takes ~2 minutes. You'll get a URL like:

```
https://helios-app.pages.dev
```

(or a random subdomain — you can set a custom subdomain in Pages settings)

---

## Step 5 — Update Railway CORS

The Railway backend only allows requests from the origins in its `CORS_ORIGINS` variable.
Add your new Cloudflare Pages URL:

```bash
cd helios-app/backend
railway variables set "CORS_ORIGINS=http://localhost:5173,https://helios-app-six.vercel.app,https://helios-app.pages.dev"
```

Replace `helios-app.pages.dev` with your actual Cloudflare subdomain.

Railway auto-redeploys when env vars change — no manual redeploy needed.

---

## Step 6 — Update Supabase Allowed URLs

Supabase blocks auth redirects to unrecognised URLs.

1. Go to [Supabase Dashboard](https://supabase.com/dashboard/project/zciyjaaigefeearpzsip) → **Authentication** → **URL Configuration**
2. Under **Redirect URLs**, add:
   ```
   https://helios-app.pages.dev/**
   ```
3. Under **Site URL**, update to your Cloudflare URL if this is now the primary domain:
   ```
   https://helios-app.pages.dev
   ```
4. Click **Save**

---

## Step 7 — Smoke Test

1. Open `https://helios-app.pages.dev` — the app should load with globe, weather data, and all panels
2. Sign in with your test account — auth should work (no redirect errors)
3. Send a chat message while logged in — DevTools Network tab should show `POST https://helios-backend-production.up.railway.app/api/chat/send`
4. Sign out — the guest path should still work (direct LLM call, no backend)

---

## Optional — Custom Domain

1. In Cloudflare Pages → your project → **Custom domains** → **Set up a custom domain**
2. Enter your domain (e.g., `app.helios.ai`)
3. Cloudflare automatically provisions SSL and adds the DNS record (if your domain is on Cloudflare DNS)
4. After the domain is live, add it to Railway CORS and Supabase Redirect URLs as in Steps 5–6

---

## Vercel

Once Cloudflare Pages is confirmed working, you can leave the Vercel deployment running as a fallback or remove it — there is no functional difference. If you remove it, also remove `https://helios-app-six.vercel.app` from Railway's `CORS_ORIGINS`.
