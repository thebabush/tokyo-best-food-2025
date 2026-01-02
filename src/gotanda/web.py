"""Flask web application for restaurant search and map view."""

from flask import Flask, render_template, request, jsonify
import folium
from folium.plugins import MarkerCluster
from .database import RestaurantDB


def create_app(db_path: str = 'restaurants.db'):
    """Create Flask application.

    Args:
        db_path: Path to SQLite database

    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    app.config['DATABASE'] = db_path

    def get_db():
        """Get database connection."""
        return RestaurantDB(app.config['DATABASE'])

    @app.route('/')
    def index():
        """Main page with map and search."""
        db = get_db()
        stats = db.get_stats()
        db.close()
        return render_template('index.html', stats=stats)

    @app.route('/api/search')
    def search():
        """Search API endpoint."""
        query = request.args.get('q', '')
        category = request.args.get('category', '')
        region = request.args.get('region', '')
        min_rating = request.args.get('min_rating', type=float)
        price_range = request.args.get('price_range', '')
        limit = request.args.get('limit', 100, type=int)
        south = request.args.get('south', type=float)
        west = request.args.get('west', type=float)
        north = request.args.get('north', type=float)
        east = request.args.get('east', type=float)

        db = get_db()
        results = db.search_restaurants(
            query=query if query else None,
            category=category if category else None,
            region=region if region else None,
            min_rating=min_rating,
            price_range=price_range if price_range else None,
            limit=limit,
            south=south,
            west=west,
            north=north,
            east=east
        )
        db.close()

        return jsonify(results)

    @app.route('/api/restaurants')
    def get_restaurants():
        """Get all restaurants with coordinates as JSON."""
        db = get_db()
        restaurants = db.get_all_restaurants_with_coords()
        db.close()

        # Format for frontend
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

        return jsonify(restaurant_data)

    @app.route('/api/categories')
    def get_categories():
        """Get all unique categories."""
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute('SELECT DISTINCT name FROM categories ORDER BY name')
        categories = [row[0] for row in cursor.fetchall()]
        db.close()
        return jsonify(categories)

    @app.route('/api/stats')
    def get_stats():
        """Get database statistics."""
        db = get_db()
        stats = db.get_stats()
        db.close()
        return jsonify(stats)

    return app


def run_server(db_path: str = 'restaurants.db', host: str = '0.0.0.0', port: int = 5000, debug: bool = True):
    """Run the Flask development server.

    Args:
        db_path: Path to SQLite database
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    app = create_app(db_path)
    app.run(host=host, port=port, debug=debug)
