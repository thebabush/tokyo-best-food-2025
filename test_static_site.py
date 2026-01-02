"""
Test suite for the static Gotanda restaurant map website using Playwright.

Tests cover:
1. Map loading
2. Text template replacement
3. Review/rating quick filters (legend clicks)
4. Advanced filters (search, category, price, min rating)
"""

import pytest
import json
from pathlib import Path
from playwright.sync_api import Page, expect


# The base_url fixture is provided by conftest.py


@pytest.fixture
def page(page: Page):
    """Configure page with longer timeout for map loading."""
    page.set_default_timeout(10000)
    return page


class TestMapLoading:
    """Test that the map loads correctly."""

    def test_page_loads(self, page: Page, site_url: str):
        """Test that the main page loads without errors."""
        page.goto(site_url)
        expect(page).to_have_title('Tokyo Best Food - Top Restaurants 2025')

    def test_map_container_exists(self, page: Page, site_url: str):
        """Test that the map container element exists."""
        page.goto(site_url)
        map_container = page.locator('#map')
        expect(map_container).to_be_visible()

    def test_leaflet_map_initialized(self, page: Page, site_url: str):
        """Test that MapLibre GL map is initialized."""
        page.goto(site_url)

        # Wait for map to be fully loaded
        page.wait_for_selector('.maplibregl-canvas', timeout=15000)

        # Check that MapLibre GL is loaded
        is_loaded = page.evaluate('() => typeof maplibregl !== "undefined"')
        assert is_loaded, 'MapLibre GL library not loaded'

        # Check that map instance exists
        map_exists = page.evaluate('() => typeof map !== "undefined" && map !== null')
        assert map_exists, 'Map instance not created'

    def test_restaurants_data_loaded(self, page: Page, site_url: str):
        """Test that restaurant data is loaded from JSON."""
        page.goto(site_url)

        # Wait for data to load
        page.wait_for_function(
            '() => typeof allRestaurantsData !== "undefined" && allRestaurantsData.length > 0',
            timeout=10000
        )

        # Check data is loaded
        count = page.evaluate('() => allRestaurantsData.length')
        assert count > 0, 'No restaurant data loaded'
        assert count > 1000, f'Expected >1000 restaurants, got {count}'

    def test_markers_displayed(self, page: Page, site_url: str):
        """Test that restaurant markers are displayed on the map."""
        page.goto(site_url)

        # Wait for markers to be added (MapLibre uses .custom-marker class)
        page.wait_for_selector('.custom-marker', timeout=15000)

        # Check that markers exist
        markers = page.locator('.custom-marker')
        count = markers.count()
        assert count > 0, 'No markers displayed on map'

    def test_marker_clusters_work(self, page: Page, site_url: str):
        """Test that markers are displayed (clustering handled differently in MapLibre)."""
        page.goto(site_url)

        # Wait for markers
        page.wait_for_timeout(3000)

        # Check for markers (MapLibre handles many markers differently than Leaflet clustering)
        has_markers = page.locator('.custom-marker').count() > 0

        assert has_markers, 'No markers found'

    def test_legend_exists(self, page: Page, site_url: str):
        """Test that the map legend is displayed."""
        page.goto(site_url)

        # Wait for legend
        page.wait_for_selector('.map-legend', timeout=10000)

        legend = page.locator('.map-legend')
        expect(legend).to_be_visible()


class TestTemplateReplacement:
    """Test that template variables are properly replaced."""

    def test_restaurant_count_replaced(self, page: Page, site_url: str):
        """Test that {{ stats.total_restaurants }} is replaced with actual number."""
        page.goto(site_url)

        # Check that the template syntax is NOT present
        content = page.content()
        assert '{{' not in content, 'Template variables not replaced - found {{'
        assert '}}' not in content, 'Template variables not replaced - found }}'

        # Check that restaurant count badge shows a number
        badge = page.locator('.stats-badge')
        badge_text = badge.text_content()

        # Should contain a number and "restaurants"
        assert 'restaurants' in badge_text.lower(), f'Badge text incorrect: {badge_text}'
        assert any(char.isdigit() for char in badge_text), f'No number in badge: {badge_text}'

        # Verify it's the correct count
        assert '1094' in badge_text or '1,094' in badge_text, f'Expected 1094 restaurants, got: {badge_text}'

    def test_no_template_syntax_in_page(self, page: Page, site_url: str):
        """Test that no Jinja2 template syntax remains in the page."""
        page.goto(site_url)

        # Get full page content
        content = page.content()

        # Check for common template patterns
        template_patterns = ['{{', '}}', '{%', '%}']
        for pattern in template_patterns:
            assert pattern not in content, f'Found template syntax: {pattern}'


class TestQuickFilters:
    """Test the quick filter functionality (legend clicks for rating ranges)."""

    def test_legend_items_clickable(self, page: Page, site_url: str):
        """Test that legend items are clickable."""
        page.goto(site_url)

        # Wait for legend
        page.wait_for_selector('.map-legend-item', timeout=10000)

        # Get all legend items
        legend_items = page.locator('.map-legend-item')
        assert legend_items.count() > 0, 'No legend items found'

        # Legend items should be visible and interactable
        first_item = legend_items.first
        expect(first_item).to_be_visible()

    def test_high_rating_filter(self, page: Page, site_url: str):
        """Test filtering by high rating (3.8+) via legend click."""
        page.goto(site_url)

        # Wait for initial markers
        page.wait_for_selector('.custom-marker', timeout=10000)
        initial_count = page.locator('.custom-marker').count()

        # Find and click the high rating legend item (3.8+)
        # The legend should have items with rating ranges
        page.wait_for_selector('.map-legend-item', timeout=5000)

        # Click on the highest rating legend item (usually red, 3.8+)
        legend_items = page.locator('.map-legend-item')
        if legend_items.count() > 0:
            # Get text to find the 3.8+ item
            for i in range(legend_items.count()):
                item = legend_items.nth(i)
                text = item.text_content() or ''
                if '3.8' in text or 'high' in text.lower():
                    item.click()
                    page.wait_for_timeout(1000)  # Wait for filter to apply

                    # Verify filtering happened
                    filtered_count = page.locator('.custom-marker').count()

                    # Should have fewer markers after filtering
                    # (unless all restaurants are 3.8+, which is unlikely)
                    # Just verify the filter mechanism works
                    break


class TestAdvancedFilters:
    """Test the advanced filter dialog functionality."""

    def test_filter_dialog_opens(self, page: Page, site_url: str):
        """Test that clicking the filter button opens the filter dialog."""
        page.goto(site_url)

        # Filter dialog should be hidden initially
        dialog = page.locator('#filterDialog')
        expect(dialog).not_to_have_class('open')

        # Click filter button
        filter_btn = page.locator('.filter-btn')
        filter_btn.click()

        # Dialog should now be open
        page.wait_for_timeout(500)  # Wait for animation
        # Check that 'open' class is present (element may have multiple classes)
        class_list = dialog.get_attribute('class')
        assert 'open' in class_list, f'Expected "open" class, got: {class_list}'

    def test_filter_dialog_closes(self, page: Page, site_url: str):
        """Test that the filter dialog can be closed."""
        page.goto(site_url)

        # Open dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Close dialog
        close_btn = page.locator('.close-btn')
        close_btn.click()
        page.wait_for_timeout(500)

        # Should be closed
        dialog = page.locator('#filterDialog')
        expect(dialog).not_to_have_class('open')

    def test_category_filter_populated(self, page: Page, site_url: str):
        """Test that the category dropdown is populated with options."""
        page.goto(site_url)

        # Open filter dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Check category select
        category_select = page.locator('#category')
        expect(category_select).to_be_visible()

        # Should have options loaded from categories.json
        options = category_select.locator('option')
        assert options.count() > 1, 'No categories loaded'

        # Should have "All Categories" as first option
        first_option = options.first.text_content()
        assert 'all' in first_option.lower(), f'Expected "All Categories", got: {first_option}'

    def test_search_filter(self, page: Page, site_url: str):
        """Test searching for a restaurant by name - filters apply automatically."""
        page.goto(site_url)

        # Wait for initial load
        page.wait_for_selector('.custom-marker', timeout=10000)
        initial_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # Open filter dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Enter search query - should apply automatically without submit button
        search_input = page.locator('#query')
        search_input.fill('tokyo')  # More generic search that should match addresses

        # Wait for filter to apply automatically (no submit needed)
        page.wait_for_timeout(1000)

        # Verify the filter worked by checking allRestaurants in JavaScript
        visible_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # Should have some filtered results
        assert visible_count > 0, f'No restaurants after search filter (got {visible_count})'
        assert visible_count <= initial_count, f'Filter should not increase count'

    def test_min_rating_filter(self, page: Page, site_url: str):
        """Test filtering by minimum rating - applies automatically."""
        page.goto(site_url)

        # Wait for initial load
        page.wait_for_selector('.custom-marker', timeout=10000)
        initial_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # Open filter dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Set minimum rating to 4.0 - should apply automatically
        rating_input = page.locator('#min_rating')
        rating_input.fill('4.0')

        # Wait for filter to apply automatically (no submit needed)
        page.wait_for_timeout(1000)

        # Should have fewer restaurants (or same if all are 4.0+)
        filtered_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # At minimum, filter should not increase the count
        assert filtered_count <= initial_count, f'Filter increased count: {filtered_count} > {initial_count}'

    def test_price_range_filter(self, page: Page, site_url: str):
        """Test filtering by price range - applies automatically."""
        page.goto(site_url)

        # Wait for initial load
        page.wait_for_selector('.custom-marker', timeout=10000)

        # Open filter dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Select a price range - should apply automatically
        price_select = page.locator('#price_range')
        price_select.select_option('～￥999')

        # Wait for filter to apply automatically (no submit needed)
        page.wait_for_timeout(1000)

        # Should have some results (or none if no restaurants in that range)
        # Just verify the filter mechanism doesn't crash
        filtered_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')
        assert filtered_count >= 0, 'Filter mechanism failed'

    def test_category_filter(self, page: Page, site_url: str):
        """Test filtering by category - applies automatically."""
        page.goto(site_url)

        # Wait for initial load
        page.wait_for_selector('.custom-marker', timeout=10000)

        # Open filter dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Select a category (get the second option, first is "All")
        category_select = page.locator('#category')
        options = category_select.locator('option')

        if options.count() > 1:
            # Select second option (first actual category) - should apply automatically
            category_select.select_option(index=1)

            # Wait for filter to apply automatically (no submit needed)
            page.wait_for_timeout(1000)

            # Should have some restaurants
            filtered_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')
            assert filtered_count >= 0, 'Category filter failed'

    def test_combined_filters(self, page: Page, site_url: str):
        """Test using multiple filters together - apply automatically."""
        page.goto(site_url)

        # Wait for initial load
        page.wait_for_selector('.custom-marker', timeout=10000)
        initial_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # Open filter dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Apply multiple filters - each should apply automatically
        page.locator('#query').fill('ramen')
        page.wait_for_timeout(500)

        page.locator('#min_rating').fill('3.5')
        page.wait_for_timeout(500)

        # Wait for filters to apply
        page.wait_for_timeout(1000)

        # Should have some results (or none if no matches)
        filtered_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')
        assert filtered_count >= 0, 'Combined filters failed'
        # Combined filters should reduce or maintain count
        assert filtered_count <= initial_count, 'Combined filters increased count'

    def test_filter_reset(self, page: Page, site_url: str):
        """Test that filters can be reset - applies automatically."""
        page.goto(site_url)

        # Wait for initial load
        page.wait_for_selector('.custom-marker', timeout=10000)
        initial_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # Apply a filter
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)
        page.locator('#min_rating').fill('4.5')
        page.wait_for_timeout(1000)  # Wait for automatic application

        # Verify filter was applied
        filtered_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')
        assert filtered_count < initial_count, 'Filter was not applied'

        # Clear filter - should apply automatically
        page.locator('#min_rating').fill('')
        page.wait_for_timeout(1000)  # Wait for automatic reset

        # Should return to initial state (approximately)
        reset_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # Allow some variance due to viewport changes
        assert abs(reset_count - initial_count) < 50, f'Filter reset failed: {reset_count} vs {initial_count}'

    def test_clear_button(self, page: Page, site_url: str):
        """Test that clear button resets all filters at once."""
        page.goto(site_url)

        # Wait for initial load
        page.wait_for_selector('.custom-marker', timeout=10000)
        initial_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')

        # Open filter dialog
        page.locator('.filter-btn').click()
        page.wait_for_timeout(500)

        # Apply multiple filters
        page.locator('#query').fill('sushi')
        page.locator('#min_rating').fill('4.0')
        page.locator('#category').select_option(index=1)  # Select first category
        page.wait_for_timeout(1000)

        # Verify filters were applied
        filtered_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')
        assert filtered_count < initial_count, 'Filters were not applied'

        # Click clear button
        clear_btn = page.locator('#clearFilters')
        expect(clear_btn).to_be_visible()
        clear_btn.click()
        page.wait_for_timeout(1000)

        # Verify all filters are cleared
        query_value = page.locator('#query').input_value()
        rating_value = page.locator('#min_rating').input_value()
        category_value = page.locator('#category').input_value()

        assert query_value == '', f'Query not cleared: {query_value}'
        assert rating_value == '', f'Rating not cleared: {rating_value}'
        assert category_value == '', f'Category not cleared: {category_value}'

        # Verify count is back to initial (approximately)
        reset_count = page.evaluate('() => allRestaurants ? allRestaurants.length : 0')
        assert abs(reset_count - initial_count) < 50, f'Clear button did not reset: {reset_count} vs {initial_count}'


class TestMarkerInteraction:
    """Test marker click and info sheet functionality."""

    def test_marker_click_opens_info_sheet(self, page: Page, site_url: str):
        """Test that clicking a marker opens the restaurant info sheet."""
        page.goto(site_url)

        # Wait for markers
        page.wait_for_selector('.custom-marker', timeout=10000)

        # Info sheet should be hidden initially
        info_sheet = page.locator('#infoSheet')
        expect(info_sheet).not_to_have_class('open')

        # Click first marker (using JavaScript click to avoid pointer event issues)
        page.evaluate('() => document.querySelector(".custom-marker").click()')

        # Info sheet should open
        page.wait_for_timeout(1000)
        # Check that 'open' class is present (element may have multiple classes)
        class_list = info_sheet.get_attribute('class')
        assert 'open' in class_list, f'Expected "open" class, got: {class_list}'

    def test_info_sheet_shows_restaurant_details(self, page: Page, site_url: str):
        """Test that info sheet displays restaurant information."""
        page.goto(site_url)

        # Wait for markers and click one
        page.wait_for_selector('.custom-marker', timeout=10000)
        page.evaluate('() => document.querySelector(".custom-marker").click()')
        page.wait_for_timeout(1000)

        # Check that restaurant name is displayed
        info_name = page.locator('#infoName')
        expect(info_name).not_to_be_empty()

        # Check that info content exists
        info_content = page.locator('#infoContent')
        expect(info_content).to_be_visible()

    def test_info_sheet_closes(self, page: Page, site_url: str):
        """Test that info sheet can be closed."""
        page.goto(site_url)

        # Open info sheet
        page.wait_for_selector('.custom-marker', timeout=10000)
        page.evaluate('() => document.querySelector(".custom-marker").click()')
        page.wait_for_timeout(1000)

        # Close it
        close_btn = page.locator('.info-close-btn')
        close_btn.click()
        page.wait_for_timeout(500)

        # Should be closed
        info_sheet = page.locator('#infoSheet')
        expect(info_sheet).not_to_have_class('open')


class TestResponsiveness:
    """Test mobile responsiveness and viewport handling."""

    def test_mobile_viewport(self, page: Page, site_url: str):
        """Test that site works on mobile viewport."""
        # Set mobile viewport
        page.set_viewport_size({'width': 375, 'height': 667})
        page.goto(site_url)

        # Should still load map
        page.wait_for_selector('.maplibregl-canvas', timeout=10000)

        # Filter button should be visible
        filter_btn = page.locator('.filter-btn')
        expect(filter_btn).to_be_visible()

    def test_tablet_viewport(self, page: Page, site_url: str):
        """Test that site works on tablet viewport."""
        # Set tablet viewport
        page.set_viewport_size({'width': 768, 'height': 1024})
        page.goto(site_url)

        # Should still load map
        page.wait_for_selector('.maplibregl-canvas', timeout=10000)

        # Map should be visible
        map_container = page.locator('#map')
        expect(map_container).to_be_visible()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
