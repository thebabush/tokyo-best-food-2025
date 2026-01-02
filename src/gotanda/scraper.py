"""Scraper for Tabelog Hyakumeiten restaurant data."""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import re


class TabelogScraper:
    """Scraper for Tabelog Hyakumeiten awards."""

    BASE_URL = 'https://award.tabelog.com'
    HYAKUMEITEN_URL = f'{BASE_URL}/hyakumeiten/'
    TABELOG_BASE = 'https://tabelog.com'

    def __init__(self, delay: float = 1.0):
        """Initialize scraper with rate limiting.

        Args:
            delay: Delay in seconds between requests to be respectful
        """
        self.delay = delay
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )

    def get_categories(self) -> List[Dict[str, str]]:
        """Fetch all restaurant categories from Hyakumeiten main page.

        Returns:
            List of dicts with 'name', 'url', 'category', 'region'
        """
        print(f'Fetching categories from {self.HYAKUMEITEN_URL}')
        response = self.client.get(self.HYAKUMEITEN_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        categories = []

        # Find all category links
        for link in soup.find_all('a', href=re.compile(r'/hyakumeiten/\w+')):
            href = link.get('href')
            if href and href != '/hyakumeiten/':
                full_url = f'{self.BASE_URL}{href}'
                path = href.replace('/hyakumeiten/', '')

                # Parse category and region from path (e.g., 'ramen_tokyo')
                parts = path.split('_')
                category = parts[0] if parts else path
                region = parts[1] if len(parts) > 1 else 'all'

                categories.append({
                    'name': link.get_text(strip=True),
                    'url': full_url,
                    'category': category,
                    'region': region,
                    'path': path
                })

        # Remove duplicates based on URL
        seen = set()
        unique_categories = []
        for cat in categories:
            if cat['url'] not in seen:
                seen.add(cat['url'])
                unique_categories.append(cat)

        print(f'Found {len(unique_categories)} unique categories')
        return unique_categories

    def get_restaurants_from_category(self, category_url: str, category: str, region: str) -> List[Dict[str, str]]:
        """Fetch restaurant listings from a category page.

        Args:
            category_url: URL of the category page
            category: Category name (e.g., 'ramen')
            region: Region name (e.g., 'tokyo')

        Returns:
            List of dicts with basic restaurant info
        """
        time.sleep(self.delay)
        print(f'Fetching restaurants from {category_url}')

        try:
            response = self.client.get(category_url)
            response.raise_for_status()
        except Exception as e:
            print(f'Error fetching {category_url}: {e}')
            return []

        soup = BeautifulSoup(response.text, 'lxml')
        restaurants = []

        # Find all restaurant links
        for link in soup.find_all('a', href=re.compile(r'tabelog\.com/[^/]+/A\d+')):
            href = link.get('href')
            if not href:
                continue

            # Ensure full URL
            if not href.startswith('http'):
                href = f'{self.TABELOG_BASE}{href}'

            # Extract basic info from the listing
            name = link.get_text(strip=True)
            if not name:
                continue

            restaurant = {
                'name': name,
                'detail_url': href,
                'category': category,
                'region': region
            }

            # Try to find additional info in the card
            parent = link.find_parent(['div', 'li', 'article'])
            if parent:
                # Look for station info
                station_text = parent.find(string=re.compile(r'駅'))
                if station_text:
                    restaurant['station'] = station_text.strip()

                # Look for closed days
                closed_text = parent.find(string=re.compile(r'曜日'))
                if closed_text:
                    restaurant['closed'] = closed_text.strip()

            restaurants.append(restaurant)

        # Remove duplicates based on URL
        seen = set()
        unique_restaurants = []
        for rest in restaurants:
            if rest['detail_url'] not in seen:
                seen.add(rest['detail_url'])
                unique_restaurants.append(rest)

        print(f'Found {len(unique_restaurants)} restaurants in {category}_{region}')
        return unique_restaurants

    def get_restaurant_details(self, detail_url: str) -> Optional[Dict[str, any]]:
        """Fetch detailed information from a restaurant's detail page.

        Args:
            detail_url: URL of the restaurant detail page

        Returns:
            Dict with detailed restaurant information
        """
        time.sleep(self.delay)
        print(f'Fetching details from {detail_url}')

        try:
            response = self.client.get(detail_url)
            response.raise_for_status()
        except Exception as e:
            print(f'Error fetching {detail_url}: {e}')
            return None

        soup = BeautifulSoup(response.text, 'lxml')
        details = {'url': detail_url}

        # Extract name
        name_elem = soup.find('h2', class_=re.compile(r'display-name|rdheader-name'))
        if not name_elem:
            name_elem = soup.find(['h1', 'h2'], string=re.compile(r'\S+'))
        if name_elem:
            details['name'] = name_elem.get_text(strip=True)

        # Extract rating
        rating_elem = soup.find(string=re.compile(r'^\d+\.\d+$'))
        if rating_elem:
            try:
                details['rating'] = float(rating_elem.strip())
            except ValueError:
                pass

        # Extract address from JSON-LD schema or text
        address_elem = soup.find(string=re.compile(r'東京都'))
        if address_elem:
            # Check if it's part of JSON-LD schema
            addr_text = address_elem.strip()
            if addr_text.startswith('{'):
                # It's JSON, try to parse it
                try:
                    import json
                    schema = json.loads(addr_text)
                    if 'address' in schema and isinstance(schema['address'], dict):
                        # Extract components from structured data
                        addr_parts = []
                        addr_obj = schema['address']
                        if 'addressRegion' in addr_obj:
                            addr_parts.append(addr_obj['addressRegion'])
                        if 'addressLocality' in addr_obj:
                            addr_parts.append(addr_obj['addressLocality'])
                        if 'streetAddress' in addr_obj:
                            addr_parts.append(addr_obj['streetAddress'])
                        details['address'] = ''.join(addr_parts)
                except (json.JSONDecodeError, KeyError):
                    # Fall back to finding address in the page
                    pass

        # If address not found yet, try finding it in schema.org JSON-LD
        if 'address' not in details:
            for script in soup.find_all('script', type='application/ld+json'):
                if script.string:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'address' in data:
                            addr = data['address']
                            if isinstance(addr, dict):
                                addr_parts = []
                                if 'addressRegion' in addr:
                                    addr_parts.append(addr['addressRegion'])
                                if 'addressLocality' in addr:
                                    addr_parts.append(addr['addressLocality'])
                                if 'streetAddress' in addr:
                                    addr_parts.append(addr['streetAddress'])
                                details['address'] = ''.join(addr_parts)
                                break
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Extract coordinates from meta tags or scripts
        lat_elem = soup.find('meta', property='place:location:latitude')
        lon_elem = soup.find('meta', property='place:location:longitude')
        if lat_elem and lon_elem:
            try:
                details['latitude'] = float(lat_elem.get('content'))
                details['longitude'] = float(lon_elem.get('content'))
            except (ValueError, TypeError):
                pass

        # Alternative: extract from script tags
        if 'latitude' not in details:
            for script in soup.find_all('script'):
                if script.string:
                    lat_match = re.search(r'latitude["\']?\s*:\s*([\d.]+)', script.string)
                    lon_match = re.search(r'longitude["\']?\s*:\s*([\d.]+)', script.string)
                    if lat_match and lon_match:
                        try:
                            details['latitude'] = float(lat_match.group(1))
                            details['longitude'] = float(lon_match.group(1))
                            break
                        except ValueError:
                            pass

        # Extract phone
        phone_elem = soup.find(string=re.compile(r'^\d{2,4}-\d{4}-\d{4}$'))
        if phone_elem:
            details['phone'] = phone_elem.strip()

        # Extract price range from JSON-LD schema
        if 'price_range' not in details:
            for script in soup.find_all('script', type='application/ld+json'):
                if script.string:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'priceRange' in data:
                            details['price_range'] = data['priceRange']
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Extract hours
        hours_elem = soup.find(string=re.compile(r'\d{1,2}:\d{2}'))
        if hours_elem:
            details['hours'] = hours_elem.strip()

        # Extract review count
        review_elem = soup.find(string=re.compile(r'\d+件'))
        if review_elem:
            review_match = re.search(r'(\d+)件', review_elem)
            if review_match:
                details['review_count'] = int(review_match.group(1))

        return details

    def close(self):
        """Close the HTTP client."""
        self.client.close()
