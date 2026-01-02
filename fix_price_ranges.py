"""Script to fix malformed JSON price ranges in the database."""

import sqlite3
import json
import re


def fix_price_ranges(db_path='restaurants.db'):
    """Fix price ranges that contain JSON schema data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all restaurants with price ranges
    cursor.execute('SELECT id, price_range FROM restaurants WHERE price_range IS NOT NULL')
    restaurants = cursor.fetchall()

    fixed_count = 0

    for restaurant_id, price_range in restaurants:
        if price_range and price_range.strip().startswith('{'):
            # This is JSON, try to parse it
            try:
                schema = json.loads(price_range)
                if 'priceRange' in schema:
                    clean_price = schema['priceRange']

                    # Update the database
                    cursor.execute('UPDATE restaurants SET price_range = ? WHERE id = ?',
                                 (clean_price, restaurant_id))
                    fixed_count += 1
                    print(f'Fixed restaurant {restaurant_id}: {clean_price}')

            except (json.JSONDecodeError, KeyError) as e:
                print(f'Could not fix restaurant {restaurant_id}: {e}')

    conn.commit()
    conn.close()

    print(f'\n✓ Fixed {fixed_count} price ranges')


if __name__ == '__main__':
    fix_price_ranges()
