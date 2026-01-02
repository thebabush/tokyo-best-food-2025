"""Fix the static site JavaScript - simple direct approach."""

from pathlib import Path

# Read the original template
template = Path('src/gotanda/templates/index.html').read_text()

# Extract CSS
css_start = template.find('<style>') + 7
css_end = template.find('</style>')
css = template[css_start:css_end]

# Extract body HTML
body_start = template.find('<body>') + 6
body_end = template.find('<script>')
body_html = template[body_start:body_end].strip()

# Extract JavaScript
js_start = template.find('<script>') + 8
js_end = template.find('</script>')
js_code = template[js_start:js_end]

# Simple replacements for static operation
js_static = js_code.replace(
    "const MAX_RESULTS = 200;  // Maximum number of restaurants to load at once\n        const UPDATE_DELAY = 500; // Debounce delay in milliseconds\n\n        let map;",
    """const MAX_RESULTS = 200;
        const UPDATE_DELAY = 500;

        let map;
        let allRestaurantsData = [];  // All restaurants loaded at startup"""
).replace(
    "const response = await fetch('/api/categories');",
    "const response = await fetch('categories.json');"
).replace(
    "// Load initial restaurants\n                await loadRestaurantsInView();",
    """// Load all restaurants first
                const resp = await fetch('restaurants.json');
                allRestaurantsData = await resp.json();
                // Then show initial view
                await loadRestaurantsInView();"""
).replace(
    """async function loadRestaurantsInView() {
            try {
                if (!map) return;

                const bounds = map.getBounds();
                const south = bounds.getSouth();
                const west = bounds.getWest();
                const north = bounds.getNorth();
                const east = bounds.getEast();

                // Get filter values
                const query = document.getElementById('query').value;
                const category = document.getElementById('category').value;
                const min_rating = document.getElementById('min_rating').value;
                const price_range = document.getElementById('price_range').value;

                // Build query parameters
                const params = new URLSearchParams();
                params.append('south', south);
                params.append('west', west);
                params.append('north', north);
                params.append('east', east);
                params.append('limit', MAX_RESULTS);

                if (query) params.append('q', query);
                if (category) params.append('category', category);
                if (min_rating) params.append('min_rating', min_rating);
                if (price_range) params.append('price_range', price_range);

                // Fetch restaurants in current viewport
                const response = await fetch(`/api/search?${params}`);
                const restaurants = await response.json();

                // Update allRestaurants for reference
                allRestaurants = restaurants;

                // Clear existing markers
                markersLayer.clearLayers();

                // Add markers for each restaurant
                restaurants.forEach(restaurant => {
                    // Determine marker color based on rating
                    let color = '#808080'; // gray
                    if (restaurant.rating >= 3.8) {
                        color = '#e74c3c'; // red
                    } else if (restaurant.rating >= 3.5) {
                        color = '#f39c12'; // orange
                    } else if (restaurant.rating >= 3.0) {
                        color = '#3498db'; // blue
                    }

                    // Create custom icon
                    const icon = L.divIcon({
                        className: 'custom-marker',
                        html: `<div style="background-color: ${color}; width: 25px; height: 25px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
                        iconSize: [25, 25],
                        iconAnchor: [12, 12]
                    });

                    // Create marker with click to show info sheet
                    const marker = L.marker([restaurant.latitude || restaurant.lat, restaurant.longitude || restaurant.lng], { icon: icon })
                        .on('click', () => {
                            const lat = restaurant.latitude || restaurant.lat;
                            const lng = restaurant.longitude || restaurant.lng;
                            showRestaurantInfo({
                                ...restaurant,
                                lat: lat,
                                lng: lng
                            });
                        });

                    markersLayer.addLayer(marker);
                });

                console.log(`Loaded ${restaurants.length} restaurants in current view`);
            } catch (error) {
                console.error('Error loading restaurants:', error);
            }
        }""",
    """async function loadRestaurantsInView() {
            try {
                if (!map) return;

                const bounds = map.getBounds();
                const south = bounds.getSouth();
                const west = bounds.getWest();
                const north = bounds.getNorth();
                const east = bounds.getEast();

                // Get filter values
                const query = (document.getElementById('query').value || '').toLowerCase();
                const category = (document.getElementById('category').value || '').toLowerCase();
                const min_rating = parseFloat(document.getElementById('min_rating').value) || 0;
                const price_range = document.getElementById('price_range').value || '';

                // CLIENT-SIDE FILTERING from loaded data
                let restaurants = allRestaurantsData.filter(r => {
                    // Viewport bounds
                    if (r.lat < south || r.lat > north || r.lng < west || r.lng > east) return false;
                    // Text search
                    if (query) {
                        const text = `${r.name} ${r.address || ''} ${r.station || ''}`.toLowerCase();
                        if (!text.includes(query)) return false;
                    }
                    // Category
                    if (category && (!r.categories || !r.categories.toLowerCase().includes(category))) return false;
                    // Rating
                    if (min_rating > 0 && (!r.rating || r.rating < min_rating)) return false;
                    // Price
                    if (price_range && (!r.price_range || !r.price_range.includes(price_range))) return false;
                    return true;
                });

                // Limit results
                restaurants = restaurants.slice(0, MAX_RESULTS);
                allRestaurants = restaurants;

                // Clear and add markers
                markersLayer.clearLayers();
                restaurants.forEach(restaurant => {
                    let color = '#808080';
                    if (restaurant.rating >= 3.8) color = '#e74c3c';
                    else if (restaurant.rating >= 3.5) color = '#f39c12';
                    else if (restaurant.rating >= 3.0) color = '#3498db';

                    const icon = L.divIcon({
                        className: 'custom-marker',
                        html: `<div style="background-color: ${color}; width: 25px; height: 25px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
                        iconSize: [25, 25],
                        iconAnchor: [12, 12]
                    });

                    const marker = L.marker([restaurant.lat, restaurant.lng], { icon: icon })
                        .on('click', () => {
                            showRestaurantInfo(restaurant);
                        });

                    markersLayer.addLayer(marker);
                });

                console.log(`Loaded ${restaurants.length} restaurants in current view`);
            } catch (error) {
                console.error('Error loading restaurants:', error);
            }
        }"""
)

# Build complete HTML
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Gotanda - Tokyo Best Restaurants</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <style>{css}</style>
</head>
<body>
{body_html}
    <script>{js_static}</script>
</body>
</html>'''

# Save
Path('static_site/index.html').write_text(html, encoding='utf-8')
print('✅ Fixed static/index.html')
print('Test with: cd static_site && python3 -m http.server 8000')
