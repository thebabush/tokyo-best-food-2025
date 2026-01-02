# Gotanda - Tokyo Best Restaurants Map

Mobile-first interactive map of Tokyo's best restaurants from Tabelog Hyakumeiten awards.

## Features

- **Mobile-Optimized UI** - Full-screen map with slide-out filter panel
- **Smart Filtering** - Search by name, location, category, rating, and price
- **Auto-Refresh** - Map updates as you pan/zoom (viewport-based loading)
- **Lightweight** - Only 320KB of restaurant data (1,094 restaurants)
- **100% Static** - No backend required, works on GitHub Pages

## Live Demo

Visit: `https://YOUR_USERNAME.github.io/gotanda` (after deployment)

## Local Development

```bash
# Serve locally
python3 -m http.server 8000

# Open http://localhost:8000
```

## Deploying to GitHub Pages

### Option 1: Direct Upload

1. Create a new GitHub repository
2. Upload the contents of `static_site/` to the repo
3. Go to Settings → Pages
4. Set source to "main" branch, root folder
5. Your site will be live at `https://USERNAME.github.io/REPO_NAME`

### Option 2: Git Push

```bash
cd static_site
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gotanda.git
git push -u origin main
```

Then enable GitHub Pages in repository settings.

## Rebuilding Data

If you have the source database and want to rebuild:

```bash
# From project root
python3 build_complete_static.py
```

This will:
- Export slim restaurant data (0.32 MB)
- Extract and adapt the mobile-first UI
- Create a production-ready static site

## Data

- **Restaurants**: 1,094 Tokyo restaurants
- **Source**: Tabelog Hyakumeiten (百名店) awards
- **Categories**: 11 cuisine types
- **File Size**: 320KB (compressed from 26MB!)

## Technology

- **Frontend**: Vanilla JavaScript (no frameworks)
- **Map**: Leaflet.js with marker clustering
- **Mobile**: Touch-optimized, PWA-ready
- **Filtering**: Client-side (fast, works offline after initial load)

## Browser Support

- ✅ iOS Safari (recommended)
- ✅ Chrome/Edge (desktop & mobile)
- ✅ Firefox
- ✅ Samsung Internet

## License

Data sourced from Tabelog. Map data from OpenStreetMap.
