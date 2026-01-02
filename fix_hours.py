"""Fix hours field in database by parsing JSON-LD schema."""

import json
import sqlite3
from pathlib import Path


def extract_hours_from_json(hours_text):
    """Extract clean hours from JSON-LD schema or text."""
    if not hours_text:
        return None

    # If it's JSON (entire schema), clear it
    if hours_text.strip().startswith('{'):
        return None

    # If it's actual hours text, keep it
    return hours_text


def fix_hours():
    """Fix all hours in database."""
    db_path = Path('restaurants.db')
    if not db_path.exists():
        print(f'Database not found: {db_path}')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all restaurants with hours
    cursor.execute('SELECT id, name, hours FROM restaurants WHERE hours IS NOT NULL')
    restaurants = cursor.fetchall()

    print(f'Found {len(restaurants)} restaurants with hours data')

    fixed = 0
    for rest_id, name, hours in restaurants:
        clean_hours = extract_hours_from_json(hours)

        # Update if changed (including JSON -> None)
        if clean_hours != hours:
            cursor.execute('UPDATE restaurants SET hours = ? WHERE id = ?',
                         (clean_hours, rest_id))
            fixed += 1
            if fixed <= 5:  # Show first 5 examples
                print(f'\n{name}:')
                print(f'  Before: {hours[:100]}...')
                print(f'  After: {clean_hours if clean_hours else "(cleared)"}')

    conn.commit()
    conn.close()

    print(f'\n✅ Fixed {fixed} hours entries')


if __name__ == '__main__':
    fix_hours()
