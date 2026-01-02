
// Static site - all data loaded from JSON files
document.getElementById('app').innerHTML = `<header>
        <h1>🍜 Gotanda - Tokyo Best Restaurants</h1>
        <p class="subtitle">Explore Tabelog's Hyakumeiten (百名店) award-winning restaurants</p>
    </header>

    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_restaurants or 0 }}</div>
                <div class="stat-label">Total Restaurants</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.restaurants_with_coords or 0 }}</div>
                <div class="stat-label">On Map</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_categories or 0 }}</div>
                <div class="stat-label">Categories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.avg_rating or 'N/A' }}</div>
                <div class="stat-label">Average Rating</div>
            </div>
        </div>

        <div class="search-section">
            <form class="search-form" onsubmit="searchRestaurants(event)">
                <div class="form-group">
                    <label for="query">Search</label>
                    <input type="text" id="query" placeholder="Restaurant name, area, or station...">
                </div>
                <div class="form-group">
                    <label for="category">Category</label>
                    <select id="category">
                        <option value="">All Categories</option>
                        <!-- Categories will be loaded dynamically -->
                    </select>
                </div>
                <div class="form-group">
                    <label for="region">Region</label>
                    <input type="text" id="region" placeholder="e.g., tokyo">
                </div>
                <div class="form-group">
                    <label for="min_rating">Min Rating</label>
                    <input type="number" id="min_rating" step="0.1" min="0" max="5" placeholder="3.5">
                </div>
                <div class="form-group">
                    <label for="price_range">Price Range</label>
                    <select id="price_range">
                        <option value="">Any</option>
                        <option value="～￥999">～￥999</option>
                        <option value="￥1,000～￥1,999">￥1,000～￥1,999</option>
                        <option value="￥3,000～￥3,999">￥3,000～￥3,999</option>
                        <option value="￥6,000～￥7,999">￥6,000～￥7,999</option>
                        <option value="￥10,000～￥14,999">￥10,000～￥14,999</option>
                        <option value="￥15,000～￥19,999">￥15,000～￥19,999</option>
                        <option value="￥20,000～￥29,999">￥20,000～￥29,999</option>
                        <option value="￥30,000+">￥30,000+</option>
                    </select>
                </div>
                <button type="submit">Search</button>
            </form>
        </div>

        <div class="map-container">
            <div id="map"></div>
        </div>

        <div class="results" id="results" style="display: none;">
            <h2>Search Results</h2>
            <div class="results-grid" id="results-grid"></div>
        </div>
    </div>`;


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



