"""Build complete static site from Flask template - mobile-first, GitHub Pages ready."""

import json
import re
from pathlib import Path
from src.gotanda.database import RestaurantDB


def parse_price_range(price_field):
    """Extract actual price range from schema.org JSON blob."""
    if not price_field:
        return None
    try:
        data = json.loads(price_field)
        if isinstance(data, dict) and 'priceRange' in data:
            return data['priceRange']
        return None
    except (json.JSONDecodeError, TypeError):
        if price_field and len(price_field) < 100:
            return price_field
        return None


def build_complete_static(db_path='restaurants.db', output_dir='static_site'):
    """Build complete static site."""
    output = Path(output_dir)
    output.mkdir(exist_ok=True)

    print('🏗️  Building complete static site for GitHub Pages...\n')

    # 1. Export slim data
    print('📦 Exporting data...')
    db = RestaurantDB(db_path)
    restaurants = db.get_all_restaurants_with_coords()

    slim_data = []
    for r in restaurants:
        if r['latitude'] and r['longitude']:
            # Address is already clean in DB (not in price_range anymore)
            clean_price = parse_price_range(r['price_range'])
            slim_data.append({
                'name': r['name'],
                'lat': r['latitude'],
                'lng': r['longitude'],
                'rating': r['rating'],
                'categories': r['categories'],
                'address': r['address'],  # Already clean
                'station': r['station'],
                'price_range': clean_price,
                'url': r['url']
            })

    # Save restaurants.json
    with open(output / 'restaurants.json', 'w', encoding='utf-8') as f:
        json.dump(slim_data, f, ensure_ascii=False, separators=(',', ':'))

    file_size = (output / 'restaurants.json').stat().st_size / (1024 * 1024)
    print(f'✓ Exported {len(slim_data)} restaurants ({file_size:.2f} MB)')

    # Save categories.json
    cursor = db.conn.cursor()
    cursor.execute('SELECT DISTINCT name FROM categories ORDER BY name')
    categories = [row[0] for row in cursor.fetchall()]
    with open(output / 'categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f'✓ Exported {len(categories)} categories')

    db.close()

    # 2. Extract and adapt template
    print('\n📝 Creating static HTML...')
    template_path = Path('src/gotanda/templates/index.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Extract CSS (between <style> and </style>)
    css_match = re.search(r'<style>(.*?)</style>', template, re.DOTALL)
    css = css_match.group(1) if css_match else ''

    # Extract body HTML (between <body> and <script>)
    body_match = re.search(r'<body>(.*?)<script>', template, re.DOTALL)
    body_html = body_match.group(1).strip() if body_match else ''

    # Extract JavaScript (between <script> and </script>)
    js_match = re.search(r'<script>(.*?)</script>', template, re.DOTALL)
    js_code = js_match.group(1) if js_match else ''

    # Adapt JavaScript for static operation
    js_adapted = adapt_javascript_for_static(js_code)

    # Calculate stats
    stats = {
        'total_restaurants': len(slim_data),
        'restaurants_with_coords': len(slim_data),
        'total_categories': len(categories),
        'avg_rating': round(sum(r['rating'] for r in slim_data if r.get('rating')) / len([r for r in slim_data if r.get('rating')]), 2) if slim_data else 0
    }

    # Save stats
    with open(output / 'stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Replace template variables in body HTML
    body_html = body_html.replace(
        '{{ stats.total_restaurants or 0 }}', str(stats['total_restaurants'])
    )

    # Extract head content (meta tags, title, library links)
    head_match = re.search(r'<head>(.*?)</head>', template, re.DOTALL)
    if head_match:
        head_content = head_match.group(1)
        # Remove the style tag from head as we extract it separately
        head_content = re.sub(r'<style>.*?</style>', '', head_content, flags=re.DOTALL)
        head_content = head_content.strip()
    else:
        head_content = '''<meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Tokyo Best Food</title>'''

    # Create complete HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    {head_content}
    <style>{css}</style>
</head>
<body>
{body_html}
    <script>{js_adapted}</script>
</body>
</html>'''

    # Save HTML
    with open(output / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print('✓ Created index.html')
    print(f'\n✅ Static site ready in {output_dir}/')
    print(f'\nTo test locally:')
    print(f'  cd {output_dir}')
    print(f'  python3 -m http.server 8000')
    print(f'  Open http://localhost:8000')
    print(f'\nTo deploy to GitHub Pages:')
    print(f'  1. Create a new repo on GitHub')
    print(f'  2. Push the {output_dir}/ folder')
    print(f'  3. Enable Pages in repo settings')


def adapt_javascript_for_static(js_code):
    """Adapt JavaScript to load from static JSON files."""

    # The template is already adapted for static operation with MapLibre GL JS
    # Just add the initial data loading setup at the start

    js_adapted = '''
        // Static site - load all data at startup
        let allRestaurantsData = [];

        async function loadAllRestaurants() {
            const response = await fetch('restaurants.json');
            allRestaurantsData = await response.json();
            return allRestaurantsData;
        }

        ''' + js_code

    # Replace API calls for categories
    js_adapted = js_adapted.replace(
        "const response = await fetch('/api/categories');",
        "const response = await fetch('categories.json');"
    )

    return js_adapted


if __name__ == '__main__':
    build_complete_static()
