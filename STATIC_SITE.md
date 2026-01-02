# Static Site Generation

## Mobile-First UI ✅

The UI is now **mobile-first** with:
- Responsive design that works on phones, tablets, and desktops
- Smaller text and spacing on mobile
- Stacked form layout on mobile (vertical)
- Shorter map height on mobile (400px vs 700px)
- Touch-friendly interactions (`:active` instead of `:hover`)
- Prevents iOS zoom with 16px font size on inputs
- Grid that becomes single column on mobile

## Fully Static Website 🚀

### How Hard Is It?

**Very easy!** The website is already ~90% static-compatible because:
- ✅ Map uses Leaflet.js (client-side JavaScript)
- ✅ All data can be exported to JSON files
- ✅ Search can be done client-side in JavaScript
- ✅ No user accounts or dynamic content
- ✅ No server-side rendering needed

### Why Go Static?

**Benefits:**
- 💰 **Free hosting** (GitHub Pages, Netlify, Vercel)
- ⚡ **Blazing fast** (CDN-served, no server delays)
- 🔒 **More secure** (no server to hack)
- 📱 **Works offline** (with service workers)
- 🌍 **Global CDN** (low latency everywhere)
- 💪 **Handles unlimited traffic** (no server scaling issues)

**Limitations:**
- ❌ Can't scrape live data (need to regenerate periodically)
- ❌ All data is public (no authentication)
- ❌ Data updates require rebuild + redeploy

### Generate Static Site

```bash
# Generate the static site
uv run python generate_static.py

# This creates a static_site/ folder with:
# - index.html (main page)
# - styles.css (all CSS)
# - app.js (all JavaScript + client-side search)
# - restaurants.json (all restaurant data)
# - categories.json (all categories)
# - stats.json (database stats)
```

### Test Locally

```bash
cd static_site
python -m http.server 8000
# Open http://localhost:8000
```

### Deploy Options

#### Option 1: GitHub Pages (Free)

```bash
# 1. Create a new repo
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/gotanda.git
git push -u origin main

# 2. Enable GitHub Pages
# Go to repo Settings → Pages
# Source: Deploy from branch
# Branch: main, folder: /static_site
# Your site will be at https://USERNAME.github.io/gotanda/
```

#### Option 2: Netlify (Free)

```bash
# 1. Install Netlify CLI
npm install -g netlify-cli

# 2. Deploy
cd static_site
netlify deploy --prod
# Follow prompts, your site goes live instantly!
```

#### Option 3: Vercel (Free)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
cd static_site
vercel --prod
# Your site is live!
```

### Update Workflow

When you scrape new restaurants:

```bash
# 1. Scrape new data
uv run gotanda scrape --tokyo-only

# 2. Regenerate static site
uv run python generate_static.py

# 3. Deploy
cd static_site
git add .
git commit -m "Update restaurant data"
git push  # Auto-deploys on GitHub Pages/Netlify/Vercel
```

### How It Works

**Before (Dynamic Flask App):**
```
User → Flask Server → SQLite Database → JSON Response → Browser
```

**After (Static Site):**
```
User → CDN → JSON Files → Browser (all filtering in JavaScript)
```

**File Structure:**
```
static_site/
├── index.html          # Main HTML
├── styles.css          # All CSS
├── app.js              # All JavaScript + search logic
├── restaurants.json    # All restaurant data (~300 restaurants ≈ 500KB)
├── categories.json     # Category list (~20 categories ≈ 1KB)
└── stats.json          # Database stats (≈ 1KB)
```

### Performance

- **Initial load:** Download ~500KB JSON + libraries
- **Search:** Instant (JavaScript filters in memory)
- **Map:** Same performance as Flask version
- **Hosting:** Free + CDN-accelerated globally

### Hybrid Approach

You could also:
1. Keep Flask for scraping/admin
2. Deploy static site for public use
3. Run scraper periodically (cron job)
4. Auto-regenerate and deploy static site

This gives you the best of both worlds!

## Comparison

| Feature | Flask (Current) | Static Site |
|---------|----------------|-------------|
| Hosting Cost | $5-20/month | **Free** |
| Setup Complexity | Medium | **Easy** |
| Performance | Good | **Excellent** |
| Scalability | Limited | **Unlimited** |
| Maintenance | Ongoing | **Minimal** |
| Live Scraping | ✅ Yes | ❌ No |
| Authentication | ✅ Possible | ❌ Not really |
| Real-time Updates | ✅ Yes | ❌ No |
| Offline Support | ❌ No | ✅ With PWA |

## Recommendation

For a **restaurant database** that updates periodically:
- ✅ **Static site is perfect!**
- Restaurants don't change hourly
- Free hosting saves money
- Blazing fast performance
- Easy to maintain

Update the data weekly/monthly, regenerate, and redeploy. Done!
