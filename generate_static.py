"""Generate a fully static website from the database."""

import json
from pathlib import Path
from src.gotanda.database import RestaurantDB


def generate_static_site(db_path='restaurants.db', output_dir='static_site'):
    """Generate a static website with all data as JSON files.

    This creates a fully static site that can be hosted on:
    - GitHub Pages
    - Netlify
    - Vercel
    - Any static hosting service

    No server required!
    """
    output = Path(output_dir)
    output.mkdir(exist_ok=True)

    db = RestaurantDB(db_path)

    print('Generating static site...\n')

    # 1. Export all restaurants with coordinates
    print('Exporting restaurants...')
    restaurants = db.get_all_restaurants_with_coords()
    restaurant_data = []
    for r in restaurants:
        if r['latitude'] and r['longitude']:
            restaurant_data.append({
                'name': r['name'],
                'lat': r['latitude'],
                'lng': r['longitude'],
                'rating': r['rating'],
                'categories': r['categories'],
                'address': r['address'],
                'station': r['station'],
                'price_range': r['price_range'],
                'hours': r['hours'],
                'closed': r['closed'],
                'phone': r['phone'],
                'url': r['url']
            })

    with open(output / 'restaurants.json', 'w', encoding='utf-8') as f:
        json.dump(restaurant_data, f, ensure_ascii=False, indent=2)
    print(f'✓ Exported {len(restaurant_data)} restaurants')

    # 2. Export categories
    print('Exporting categories...')
    cursor = db.conn.cursor()
    cursor.execute('SELECT DISTINCT name FROM categories ORDER BY name')
    categories = [row[0] for row in cursor.fetchall()]

    with open(output / 'categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f'✓ Exported {len(categories)} categories')

    # 3. Export stats
    print('Exporting stats...')
    stats = db.get_stats()

    with open(output / 'stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f'✓ Exported stats')

    # 4. Create static HTML
    print('Creating static HTML...')
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gotanda - Tokyo Best Restaurants Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div id="app">Loading...</div>
    <script src="app.js"></script>
</body>
</html>'''

    with open(output / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    print('✓ Created index.html')

    # 5. Copy CSS from template
    print('Extracting CSS...')
    with open('src/gotanda/templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
        # Extract CSS between <style> and </style>
        css_start = content.find('<style>') + 7
        css_end = content.find('</style>')
        css = content[css_start:css_end]

    with open(output / 'styles.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print('✓ Extracted CSS')

    # 6. Create JavaScript app
    print('Creating JavaScript app...')
    with open('src/gotanda/templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
        # Extract body HTML
        body_start = content.find('<body>') + 6
        body_end = content.find('</body>')
        body_html = content[body_start:body_end]
        # Remove script tags to extract separately
        script_start = body_html.find('<script>')
        body_html = body_html[:script_start].strip()

        # Extract JavaScript
        js_start = content.find('<script>') + 8
        js_end = content.find('</script>')
        js_code = content[js_start:js_end]

    # Modify JS to load from JSON files instead of API
    js_modified = js_code.replace(
        "const response = await fetch('/api/categories');",
        "const response = await fetch('categories.json');"
    ).replace(
        "const response = await fetch('/api/restaurants');",
        "const response = await fetch('restaurants.json');"
    ).replace(
        "const response = await fetch(`/api/search?${params}`);",
        "// Client-side search\\nconst allRestaurants = await (await fetch('restaurants.json')).json();\\nconst restaurants = filterRestaurants(allRestaurants, query, category, region, min_rating, price_range);"
    )

    # Add client-side search function
    search_function = '''
function filterRestaurants(restaurants, query, category, region, min_rating, price_range) {
    return restaurants.filter(r => {
        if (query && !r.name.toLowerCase().includes(query.toLowerCase()) &&
            !r.address?.toLowerCase().includes(query.toLowerCase()) &&
            !r.station?.toLowerCase().includes(query.toLowerCase())) {
            return false;
        }
        if (category && !r.categories?.toLowerCase().includes(category.toLowerCase())) {
            return false;
        }
        if (region && !r.station?.toLowerCase().includes(region.toLowerCase())) {
            return false;
        }
        if (min_rating && (!r.rating || r.rating < min_rating)) {
            return false;
        }
        if (price_range && !r.price_range?.includes(price_range)) {
            return false;
        }
        return true;
    }).slice(0, 100);
}
'''

    full_js = f'''
// Static site - all data loaded from JSON files
document.getElementById('app').innerHTML = `{body_html}`;

{search_function}

{js_modified}
'''

    with open(output / 'app.js', 'w', encoding='utf-8') as f:
        f.write(full_js)
    print('✓ Created app.js with client-side search')

    db.close()

    print(f'\n✅ Static site generated in {output_dir}/')
    print('\nTo serve locally:')
    print(f'  cd {output_dir}')
    print('  python -m http.server 8000')
    print('  # Then open http://localhost:8000')
    print('\nTo deploy:')
    print('  - Upload to GitHub Pages')
    print('  - Deploy to Netlify/Vercel')
    print('  - Host on any static file server')
    print('\n💡 No backend needed - 100% static!')


if __name__ == '__main__':
    generate_static_site()
