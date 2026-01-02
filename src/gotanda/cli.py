"""Command-line interface for Gotanda."""

import argparse
import sys
from pathlib import Path
from .scraper import TabelogScraper
from .database import RestaurantDB
from .web import run_server


def scrape_command(args):
    """Run the scraper to populate database."""
    print(f'Starting scraper...')
    print(f'Database: {args.db}')
    print(f'Delay between requests: {args.delay}s')
    print(f'Focus on Tokyo only: {args.tokyo_only}')
    print()

    # Initialize scraper and database
    scraper = TabelogScraper(delay=args.delay)
    db = RestaurantDB(args.db)

    try:
        # Get all categories
        categories = scraper.get_categories()
        print(f'Found {len(categories)} categories\n')

        # Filter to Tokyo-only if requested
        if args.tokyo_only:
            categories = [c for c in categories if c['region'] == 'tokyo']
            print(f'Filtering to Tokyo categories: {len(categories)} categories\n')

        total_restaurants = 0

        # Process each category
        for i, category_info in enumerate(categories, 1):
            print(f"\n[{i}/{len(categories)}] Processing {category_info['category']}_{category_info['region']}...")

            # Get category ID
            category_id = db.insert_category(
                name=category_info['category'],
                name_en=category_info['category']
            )

            # Get restaurants from category page
            restaurants = scraper.get_restaurants_from_category(
                category_info['url'],
                category_info['category'],
                category_info['region']
            )

            print(f'Found {len(restaurants)} restaurants in this category')

            # Get details for each restaurant
            for j, restaurant in enumerate(restaurants, 1):
                if args.limit and total_restaurants >= args.limit:
                    print(f'\nReached limit of {args.limit} restaurants')
                    break

                print(f'  [{j}/{len(restaurants)}] {restaurant["name"]}...')

                # Get detailed info
                details = scraper.get_restaurant_details(restaurant['detail_url'])

                if details:
                    # Merge basic info with details
                    full_info = {**restaurant, **details}

                    # Insert restaurant
                    restaurant_id = db.insert_restaurant(full_info)

                    if restaurant_id:
                        # Link to category
                        db.link_restaurant_category(
                            restaurant_id,
                            category_id,
                            category_info['region']
                        )
                        total_restaurants += 1
                        print(f'    ✓ Saved (ID: {restaurant_id})')
                    else:
                        print(f'    ✗ Failed to save')
                else:
                    print(f'    ✗ Failed to get details')

            if args.limit and total_restaurants >= args.limit:
                break

        # Print final statistics
        print('\n' + '='*60)
        print('SCRAPING COMPLETE')
        print('='*60)
        stats = db.get_stats()
        print(f"Total restaurants in database: {stats['total_restaurants']}")
        print(f"Restaurants with coordinates: {stats['restaurants_with_coords']}")
        print(f"Total categories: {stats['total_categories']}")
        print(f"Average rating: {stats['avg_rating']}")
        print('='*60)

    finally:
        scraper.close()
        db.close()


def serve_command(args):
    """Run the web server."""
    print(f'Starting web server...')
    print(f'Database: {args.db}')
    print(f'URL: http://{args.host}:{args.port}')
    print()

    db = RestaurantDB(args.db)
    stats = db.get_stats()
    db.close()

    print(f"Serving {stats['total_restaurants']} restaurants")
    print('Press Ctrl+C to stop\n')

    run_server(
        db_path=args.db,
        host=args.host,
        port=args.port,
        debug=args.debug
    )


def stats_command(args):
    """Show database statistics."""
    db = RestaurantDB(args.db)
    stats = db.get_stats()
    db.close()

    print('\n' + '='*60)
    print('DATABASE STATISTICS')
    print('='*60)
    print(f"Total restaurants: {stats['total_restaurants']}")
    print(f"Restaurants with coordinates: {stats['restaurants_with_coords']}")
    print(f"Total categories: {stats['total_categories']}")
    print(f"Average rating: {stats['avg_rating']}")
    print('='*60 + '\n')


def search_command(args):
    """Search restaurants from command line."""
    db = RestaurantDB(args.db)

    results = db.search_restaurants(
        query=args.query,
        category=args.category,
        region=args.region,
        min_rating=args.min_rating,
        limit=args.limit
    )

    db.close()

    if not results:
        print('No restaurants found')
        return

    print(f'\nFound {len(results)} restaurants:\n')

    for i, restaurant in enumerate(results, 1):
        print(f"{i}. {restaurant['name']}")
        if restaurant['rating']:
            print(f"   Rating: ⭐ {restaurant['rating']}")
        if restaurant['categories']:
            print(f"   Categories: {restaurant['categories']}")
        if restaurant['address']:
            print(f"   Address: {restaurant['address']}")
        if restaurant['station']:
            print(f"   Station: {restaurant['station']}")
        if restaurant['url']:
            print(f"   URL: {restaurant['url']}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Gotanda - Tabelog Hyakumeiten scraper and restaurant database'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape restaurants and populate database')
    scrape_parser.add_argument('--db', default='restaurants.db', help='Database file path')
    scrape_parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    scrape_parser.add_argument('--tokyo-only', action='store_true', help='Only scrape Tokyo restaurants')
    scrape_parser.add_argument('--limit', type=int, help='Maximum number of restaurants to scrape')
    scrape_parser.set_defaults(func=scrape_command)

    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Run web server')
    serve_parser.add_argument('--db', default='restaurants.db', help='Database file path')
    serve_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    serve_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    serve_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    serve_parser.set_defaults(func=serve_command)

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--db', default='restaurants.db', help='Database file path')
    stats_parser.set_defaults(func=stats_command)

    # Search command
    search_parser = subparsers.add_parser('search', help='Search restaurants')
    search_parser.add_argument('query', nargs='?', help='Search query')
    search_parser.add_argument('--category', help='Filter by category')
    search_parser.add_argument('--region', help='Filter by region')
    search_parser.add_argument('--min-rating', type=float, help='Minimum rating')
    search_parser.add_argument('--limit', type=int, default=20, help='Maximum results')
    search_parser.add_argument('--db', default='restaurants.db', help='Database file path')
    search_parser.set_defaults(func=search_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
