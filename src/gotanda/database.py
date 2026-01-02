"""SQLite database for storing restaurant information."""

import sqlite3
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class RestaurantDB:
    """SQLite database for Tabelog Hyakumeiten restaurants."""

    def __init__(self, db_path: str = 'restaurants.db'):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Main restaurants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_reading TEXT,
                address TEXT,
                latitude REAL,
                longitude REAL,
                phone TEXT,
                rating REAL,
                review_count INTEGER,
                price_range TEXT,
                hours TEXT,
                closed TEXT,
                station TEXT,
                url TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Categories table (many-to-many relationship)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                name_en TEXT
            )
        ''')

        # Restaurant-Category junction table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurant_categories (
                restaurant_id INTEGER,
                category_id INTEGER,
                region TEXT,
                PRIMARY KEY (restaurant_id, category_id),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        ''')

        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_coords ON restaurants(latitude, longitude)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name)')

        self.conn.commit()

    def insert_category(self, name: str, name_en: Optional[str] = None) -> int:
        """Insert or get category ID.

        Args:
            name: Category display name
            name_en: English category name

        Returns:
            Category ID
        """
        cursor = self.conn.cursor()

        # Try to get existing category
        cursor.execute('SELECT id FROM categories WHERE name = ?', (name,))
        result = cursor.fetchone()

        if result:
            return result[0]

        # Insert new category
        cursor.execute('INSERT INTO categories (name, name_en) VALUES (?, ?)', (name, name_en))
        self.conn.commit()
        return cursor.lastrowid

    def insert_restaurant(self, restaurant: Dict) -> Optional[int]:
        """Insert or update restaurant.

        Args:
            restaurant: Dict with restaurant data

        Returns:
            Restaurant ID or None if error
        """
        cursor = self.conn.cursor()

        # Check if restaurant exists by URL
        url = restaurant.get('url')
        if not url:
            return None

        cursor.execute('SELECT id FROM restaurants WHERE url = ?', (url,))
        result = cursor.fetchone()

        if result:
            # Update existing restaurant
            restaurant_id = result[0]
            self._update_restaurant(restaurant_id, restaurant)
            return restaurant_id

        # Insert new restaurant
        cursor.execute('''
            INSERT INTO restaurants (
                name, address, latitude, longitude, phone, rating,
                review_count, price_range, hours, closed, station, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            restaurant.get('name'),
            restaurant.get('address'),
            restaurant.get('latitude'),
            restaurant.get('longitude'),
            restaurant.get('phone'),
            restaurant.get('rating'),
            restaurant.get('review_count'),
            restaurant.get('price_range'),
            restaurant.get('hours'),
            restaurant.get('closed'),
            restaurant.get('station'),
            url
        ))

        self.conn.commit()
        return cursor.lastrowid

    def _update_restaurant(self, restaurant_id: int, restaurant: Dict):
        """Update existing restaurant data.

        Args:
            restaurant_id: Restaurant ID
            restaurant: Dict with updated data
        """
        cursor = self.conn.cursor()

        # Only update non-null fields
        updates = []
        values = []

        for field in ['name', 'address', 'latitude', 'longitude', 'phone', 'rating',
                      'review_count', 'price_range', 'hours', 'closed', 'station']:
            if restaurant.get(field) is not None:
                updates.append(f'{field} = ?')
                values.append(restaurant[field])

        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            values.append(restaurant_id)
            query = f"UPDATE restaurants SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            self.conn.commit()

    def link_restaurant_category(self, restaurant_id: int, category_id: int, region: Optional[str] = None):
        """Link restaurant to category.

        Args:
            restaurant_id: Restaurant ID
            category_id: Category ID
            region: Region name (e.g., 'tokyo', 'osaka')
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO restaurant_categories (restaurant_id, category_id, region)
            VALUES (?, ?, ?)
        ''', (restaurant_id, category_id, region))
        self.conn.commit()

    def search_restaurants(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
        min_rating: Optional[float] = None,
        price_range: Optional[str] = None,
        limit: int = 100,
        south: Optional[float] = None,
        west: Optional[float] = None,
        north: Optional[float] = None,
        east: Optional[float] = None
    ) -> List[Dict]:
        """Search restaurants with filters.

        Args:
            query: Text search in name or address
            category: Filter by category name
            region: Filter by region
            min_rating: Minimum rating threshold
            price_range: Filter by price range
            limit: Maximum results to return
            south: Southern latitude bound of viewport
            west: Western longitude bound of viewport
            north: Northern latitude bound of viewport
            east: Eastern longitude bound of viewport

        Returns:
            List of restaurant dicts
        """
        cursor = self.conn.cursor()

        sql = '''
            SELECT DISTINCT r.*,
                   GROUP_CONCAT(c.name, ', ') as categories,
                   GROUP_CONCAT(rc.region, ', ') as regions
            FROM restaurants r
            LEFT JOIN restaurant_categories rc ON r.id = rc.restaurant_id
            LEFT JOIN categories c ON rc.category_id = c.id
            WHERE 1=1
        '''
        params = []

        if query:
            sql += ' AND (r.name LIKE ? OR r.address LIKE ? OR r.station LIKE ?)'
            search_term = f'%{query}%'
            params.extend([search_term, search_term, search_term])

        if category:
            sql += ' AND c.name LIKE ?'
            params.append(f'%{category}%')

        if region:
            sql += ' AND rc.region = ?'
            params.append(region)

        if min_rating:
            sql += ' AND r.rating >= ?'
            params.append(min_rating)

        if price_range:
            sql += ' AND r.price_range LIKE ?'
            params.append(f'%{price_range}%')

        if south is not None and west is not None and north is not None and east is not None:
            sql += ' AND r.latitude BETWEEN ? AND ? AND r.longitude BETWEEN ? AND ?'
            params.extend([south, north, west, east])

        sql += ' GROUP BY r.id ORDER BY r.rating DESC, r.review_count DESC LIMIT ?'
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_all_restaurants_with_coords(self) -> List[Dict]:
        """Get all restaurants that have coordinates for map display.

        Returns:
            List of restaurant dicts with coordinates
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.*,
                   GROUP_CONCAT(c.name, ', ') as categories,
                   GROUP_CONCAT(rc.region, ', ') as regions
            FROM restaurants r
            LEFT JOIN restaurant_categories rc ON r.id = rc.restaurant_id
            LEFT JOIN categories c ON rc.category_id = c.id
            WHERE r.latitude IS NOT NULL AND r.longitude IS NOT NULL
            GROUP BY r.id
            ORDER BY r.rating DESC
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict:
        """Get database statistics.

        Returns:
            Dict with stats
        """
        cursor = self.conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM restaurants')
        total_restaurants = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM restaurants WHERE latitude IS NOT NULL')
        restaurants_with_coords = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM categories')
        total_categories = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(rating) FROM restaurants WHERE rating IS NOT NULL')
        avg_rating = cursor.fetchone()[0]

        return {
            'total_restaurants': total_restaurants,
            'restaurants_with_coords': restaurants_with_coords,
            'total_categories': total_categories,
            'avg_rating': round(avg_rating, 2) if avg_rating else None
        }

    def close(self):
        """Close database connection."""
        self.conn.close()
