"""Example usage of the Gotanda package."""

from src.gotanda.scraper import TabelogScraper
from src.gotanda.database import RestaurantDB


def example_scrape():
    """Example: Scrape a few restaurants."""
    print('Example 1: Scraping restaurants\n')

    scraper = TabelogScraper(delay=1.0)
    db = RestaurantDB('restaurants.db')

    # Get categories
    categories = scraper.get_categories()
    tokyo_ramen = [c for c in categories if c['category'] == 'ramen' and c['region'] == 'tokyo'][0]

    print(f"Category: {tokyo_ramen['name']}")
    print(f"URL: {tokyo_ramen['url']}\n")

    # Get restaurants from category
    restaurants = scraper.get_restaurants_from_category(
        tokyo_ramen['url'],
        tokyo_ramen['category'],
        tokyo_ramen['region']
    )

    print(f'Found {len(restaurants)} restaurants\n')

    # Get details for first restaurant
    if restaurants:
        details = scraper.get_restaurant_details(restaurants[0]['detail_url'])
        print(f"Restaurant: {details.get('name')}")
        print(f"Rating: {details.get('rating')}")
        print(f"Address: {details.get('address')}")
        print(f"Coordinates: ({details.get('latitude')}, {details.get('longitude')})\n")

    scraper.close()
    db.close()


def example_search():
    """Example: Search restaurants."""
    print('Example 2: Searching restaurants\n')

    db = RestaurantDB('restaurants.db')

    # Search for ramen
    results = db.search_restaurants(category='ramen', limit=5)

    print(f'Found {len(results)} ramen restaurants:\n')

    for r in results:
        print(f"- {r['name']} (⭐ {r['rating']})")
        print(f"  {r['address']}")
        print()

    db.close()


def example_stats():
    """Example: Get database statistics."""
    print('Example 3: Database statistics\n')

    db = RestaurantDB('restaurants.db')

    stats = db.get_stats()

    print(f"Total restaurants: {stats['total_restaurants']}")
    print(f"With coordinates: {stats['restaurants_with_coords']}")
    print(f"Categories: {stats['total_categories']}")
    print(f"Average rating: {stats['avg_rating']}\n")

    db.close()


if __name__ == '__main__':
    # Uncomment to run examples

    # example_scrape()  # Warning: Makes web requests
    example_search()
    example_stats()
