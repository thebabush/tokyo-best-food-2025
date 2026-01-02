"""Build a slim, optimized static site for GitHub Pages."""

import json
from pathlib import Path
from src.gotanda.database import RestaurantDB


def parse_address(address_field):
    """Extract clean street address from schema.org JSON blob."""
    if not address_field:
        return None

    try:
        data = json.loads(address_field)
        if isinstance(data, dict) and 'address' in data:
            addr = data['address']
            if isinstance(addr, dict):
                # Extract street address and locality
                street = addr.get('streetAddress', '')
                locality = addr.get('addressLocality', '')
                if street and locality:
                    return f"{street}, {locality}"
                return street or locality
        return None
    except (json.JSONDecodeError, TypeError):
        # If it's not JSON, return as-is (might be plain text)
        if len(address_field) < 200:  # Avoid returning huge blobs
            return address_field
        return None


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
        # If it's not JSON, return as-is (might already be clean)
        if len(price_field) < 100:  # Avoid returning huge blobs
            return price_field
        return None


def build_static_site(db_path='restaurants.db', output_dir='static_site'):
    """Generate optimized static site with slim JSON."""
    output = Path(output_dir)
    output.mkdir(exist_ok=True)

    print('🏗️  Building static site for GitHub Pages...\n')

    db = RestaurantDB(db_path)

    # 1. Export slim restaurant data
    print('📦 Exporting restaurants...')
    restaurants = db.get_all_restaurants_with_coords()
    slim_data = []

    for r in restaurants:
        if r['latitude'] and r['longitude']:
            # Parse fields to extract clean data
            clean_address = parse_address(r['address'])
            clean_price = parse_price_range(r['price_range'])

            slim_data.append({
                'name': r['name'],
                'lat': r['latitude'],
                'lng': r['longitude'],
                'rating': r['rating'],
                'categories': r['categories'],
                'address': clean_address,
                'station': r['station'],
                'price_range': clean_price,
                'url': r['url']  # Link to Tabelog
            })

    # Write slim JSON
    restaurants_file = output / 'restaurants.json'
    with open(restaurants_file, 'w', encoding='utf-8') as f:
        json.dump(slim_data, f, ensure_ascii=False, separators=(',', ':'))

    file_size = restaurants_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f'✓ Exported {len(slim_data)} restaurants')
    print(f'  File size: {size_mb:.2f} MB (was 26 MB!)')

    # 2. Export categories
    print('\n📋 Exporting categories...')
    cursor = db.conn.cursor()
    cursor.execute('SELECT DISTINCT name FROM categories ORDER BY name')
    categories = [row[0] for row in cursor.fetchall()]

    with open(output / 'categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f'✓ Exported {len(categories)} categories')

    db.close()

    print(f'\n✅ Static data exported to {output_dir}/')
    print(f'\nNext steps:')
    print(f'  1. Copy HTML/CSS/JS from Flask template')
    print(f'  2. Adapt JavaScript for client-side filtering')
    print(f'  3. Test with: cd {output_dir} && python -m http.server 8000')


if __name__ == '__main__':
    build_static_site()
