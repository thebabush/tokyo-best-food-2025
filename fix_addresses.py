"""Script to fix malformed JSON addresses in the database."""

import sqlite3
import json
import re


def fix_addresses(db_path='restaurants.db'):
    """Fix addresses that contain JSON schema data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all restaurants with addresses
    cursor.execute('SELECT id, address FROM restaurants WHERE address IS NOT NULL')
    restaurants = cursor.fetchall()

    fixed_count = 0

    for restaurant_id, address in restaurants:
        if address and address.strip().startswith('{'):
            # This is JSON, try to parse it
            try:
                schema = json.loads(address)
                if 'address' in schema and isinstance(schema['address'], dict):
                    # Extract clean address
                    addr_obj = schema['address']
                    addr_parts = []

                    if 'addressRegion' in addr_obj:
                        addr_parts.append(addr_obj['addressRegion'])
                    if 'addressLocality' in addr_obj:
                        addr_parts.append(addr_obj['addressLocality'])
                    if 'streetAddress' in addr_obj:
                        addr_parts.append(addr_obj['streetAddress'])

                    clean_address = ''.join(addr_parts)

                    if clean_address:
                        # Update the database
                        cursor.execute('UPDATE restaurants SET address = ? WHERE id = ?',
                                     (clean_address, restaurant_id))
                        fixed_count += 1
                        print(f'Fixed restaurant {restaurant_id}: {clean_address[:50]}...')

            except (json.JSONDecodeError, KeyError) as e:
                print(f'Could not fix restaurant {restaurant_id}: {e}')

    conn.commit()
    conn.close()

    print(f'\n✓ Fixed {fixed_count} addresses')


if __name__ == '__main__':
    fix_addresses()
