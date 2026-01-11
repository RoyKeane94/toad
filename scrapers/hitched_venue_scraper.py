#!/usr/bin/env python3
"""
Hitched.co.uk Wedding Venue Scraper (Playwright Version)
=========================================================
A web scraping tool to extract wedding venue names and URLs from Hitched.co.uk
Uses Playwright to handle anti-bot protection.

Setup:
    pip install playwright beautifulsoup4
    playwright install chromium

Usage:
    python hitched_venue_scraper.py
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import csv
import re

# Available regions on Hitched.co.uk
REGIONS = {
    "1": ("London", "london"),
    "2": ("North West - England", "north-west-england"),
    "3": ("Scotland", "scotland"),
    "4": ("Kent", "kent"),
    "5": ("Hampshire", "hampshire"),
    "6": ("North Yorkshire", "north-yorkshire"),
    "7": ("Surrey", "surrey"),
    "8": ("Essex", "essex"),
    "9": ("Devon", "devon"),
    "10": ("West Midlands", "west-midlands"),
    "11": ("North East - England", "north-east-england"),
    "12": ("Cheshire", "cheshire"),
    "13": ("West Yorkshire", "west-yorkshire"),
    "14": ("Cornwall", "cornwall"),
    "15": ("Hertfordshire", "hertfordshire"),
    "16": ("West Sussex", "west-sussex"),
    "17": ("Oxfordshire", "oxfordshire"),
    "18": ("Nottinghamshire", "nottinghamshire"),
    "19": ("Northern Ireland", "northern-ireland"),
}

BASE_URL = "https://www.hitched.co.uk"
VENUES_BASE = f"{BASE_URL}/wedding-venues"

# Email regex pattern
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')


def display_menu():
    """Display the region selection menu."""
    print("\n" + "=" * 60)
    print("       HITCHED.CO.UK WEDDING VENUE SCRAPER")
    print("=" * 60)
    print("\nAvailable regions:\n")
    for key, (name, _) in REGIONS.items():
        print(f"  [{key:>2}] {name}")
    print(f"\n  [ 0] Exit")
    print("=" * 60)


def get_user_choice():
    """Get the user's region choice."""
    while True:
        choice = input("\nEnter region number: ").strip()
        if choice == "0":
            return None
        if choice in REGIONS:
            return choice
        print("Invalid choice. Please enter a valid region number.")


def extract_venues_from_html(html):
    """
    Extract venue names and URLs from page HTML.
    
    Args:
        html: Raw HTML string
        
    Returns:
        List of tuples (venue_name, venue_url)
    """
    soup = BeautifulSoup(html, "html.parser")
    venues = []
    
    # Method 1: Find links with data-test-id="storefrontTitle"
    venue_links = soup.find_all("a", attrs={"data-test-id": "storefrontTitle"})
    
    # Method 2: Find links with class containing vendorTile__title
    if not venue_links:
        venue_links = soup.find_all("a", class_=lambda x: x and "vendorTile__title" in x)
    
    # Method 3: Find any link to a venue page within vendor tiles
    if not venue_links:
        tiles = soup.find_all(class_=lambda x: x and "vendorTile" in str(x))
        for tile in tiles:
            link = tile.find("a", href=lambda x: x and "/wedding-venues/" in x and "_" in x and ".htm" in x)
            if link and link not in venue_links:
                venue_links.append(link)
    
    # Method 4: Find all links matching venue URL pattern
    if not venue_links:
        venue_links = soup.find_all("a", href=re.compile(r"/wedding-venues/[^/]+_\d+\.htm"))
    
    for link in venue_links:
        href = link.get("href", "")
        name = link.get_text(strip=True)
        
        if not name or not href:
            continue
        
        # Ensure full URL
        if not href.startswith("http"):
            href = f"{BASE_URL}{href}"
        
        # Only include actual venue pages (contain _XXXX.htm pattern)
        if re.search(r"_\d+\.htm$", href):
            venues.append((name, href))
    
    return venues


def has_next_page(page):
    """Check if there's a next page button that's enabled."""
    try:
        # Try multiple selectors for next button
        selectors = [
            "span.pagination__next button:not([disabled])",
            ".pagination__next button:not([disabled])",
            "button[aria-label*='next' i]:not([disabled])",
            "button[aria-label*='Next' i]:not([disabled])",
            # Also check for enabled state via aria-disabled
            "span.pagination__next button[aria-disabled='false']",
            ".pagination__next button[aria-disabled='false']",
        ]
        
        for selector in selectors:
            try:
                next_btn = page.locator(selector).first
                if next_btn.is_visible(timeout=2000):
                    # Double-check it's not disabled via class or attribute
                    is_disabled = next_btn.get_attribute("disabled") is not None
                    aria_disabled = next_btn.get_attribute("aria-disabled") == "true"
                    classes = next_btn.get_attribute("class") or ""
                    has_disabled_class = "disabled" in classes.lower()
                    if not is_disabled and not has_disabled_class and not aria_disabled:
                        return True
            except:
                continue
        
        # Fallback: check if ANY next button exists (even without :not([disabled]))
        # and manually verify its state
        fallback_selectors = [
            "span.pagination__next button",
            ".pagination__next button",
        ]
        for selector in fallback_selectors:
            try:
                next_btn = page.locator(selector).first
                if next_btn.is_visible(timeout=1000):
                    is_disabled = next_btn.get_attribute("disabled") is not None
                    aria_disabled = next_btn.get_attribute("aria-disabled") == "true"
                    classes = next_btn.get_attribute("class") or ""
                    has_disabled_class = "disabled" in classes.lower()
                    if not is_disabled and not has_disabled_class and not aria_disabled:
                        return True
            except:
                continue
        
        return False
    except:
        return False


def click_next_page(page):
    """Click the next page button and wait for content to load."""
    try:
        # Try multiple selectors for next button
        selectors = [
            "span.pagination__next button:not([disabled])",
            ".pagination__next button:not([disabled])",
            "button[aria-label*='next' i]:not([disabled])",
            "button[aria-label*='Next' i]:not([disabled])",
            "span.pagination__next button",
            ".pagination__next button",
        ]
        
        for selector in selectors:
            try:
                next_btn = page.locator(selector).first
                if next_btn.is_visible(timeout=2000):
                    is_disabled = next_btn.get_attribute("disabled") is not None
                    aria_disabled = next_btn.get_attribute("aria-disabled") == "true"
                    classes = next_btn.get_attribute("class") or ""
                    has_disabled_class = "disabled" in classes.lower()
                    if not is_disabled and not has_disabled_class and not aria_disabled:
                        # Scroll the button into view first
                        next_btn.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        next_btn.click()
                        
                        # Wait for network activity to settle
                        try:
                            page.wait_for_load_state("networkidle", timeout=20000)
                        except:
                            pass  # Continue even if timeout
                        
                        time.sleep(3)  # Increased wait for dynamic content
                        
                        # Wait for venue listings to load - try multiple selectors
                        try:
                            page.wait_for_selector("[data-test-id='storefrontTitle']", timeout=15000)
                        except:
                            try:
                                page.wait_for_selector(".vendorTile__title", timeout=10000)
                            except:
                                try:
                                    page.wait_for_selector(".vendorTile", timeout=10000)
                                except:
                                    pass  # Continue anyway
                        
                        time.sleep(2)  # Additional delay to ensure content is loaded
                        return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"  Click error: {e}")
        return False


def get_total_pages_from_html(html):
    """Extract total page count from pagination."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Try multiple methods to find pagination
    pagination = soup.find("nav", class_="pagination")
    if not pagination:
        pagination = soup.find("nav", class_=lambda x: x and "pagination" in x.lower())
    if not pagination:
        pagination = soup.find("div", class_=lambda x: x and "pagination" in x.lower())
    
    if not pagination:
        return 1
    
    max_page = 1
    # Try multiple button selectors
    buttons = pagination.find_all("button", class_="app-pagination-link")
    if not buttons:
        buttons = pagination.find_all("button", class_=lambda x: x and "pagination" in x.lower())
    if not buttons:
        buttons = pagination.find_all("a", class_=lambda x: x and "pagination" in x.lower())
    
    for button in buttons:
        text = button.get_text(strip=True)
        if text.isdigit():
            max_page = max(max_page, int(text))
        # Also check aria-label or data attributes
        aria_label = button.get("aria-label", "")
        if "page" in aria_label.lower() and text.isdigit():
            max_page = max(max_page, int(text))
    
    return max_page


def scrape_region(region_slug, region_name):
    """
    Scrape all wedding venues from a specific region using Playwright.
    
    Args:
        region_slug: URL slug for the region
        region_name: Display name of the region
        
    Returns:
        List of tuples (venue_name, venue_url)
    """
    all_venues = []
    start_url = f"{VENUES_BASE}/{region_slug}.htm"
    
    print(f"\nLaunching browser...")
    print(f"Navigating to: {start_url}")
    
    try:
        with sync_playwright() as p:
            # Launch browser in non-headless mode (more like real user)
            print("  Starting Chromium...")
            browser = p.chromium.launch(
                headless=False,  # Show the browser - less likely to be blocked
                timeout=30000,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            print("  Browser launched successfully")
            
            # Create context with realistic settings
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-GB",
                timezone_id="Europe/London",
            )
            
            # Remove webdriver flag to avoid detection
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                # Navigate to first page
                print("  Loading page...")
                page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
                print("  Page loaded")
                
                # Give it time to fully render
                time.sleep(3)
                
                # Handle cookie consent if present
                try:
                    cookie_btn = page.locator("button:has-text('Accept')").first
                    if cookie_btn.is_visible(timeout=3000):
                        cookie_btn.click()
                        time.sleep(1)
                except:
                    pass  # No cookie banner
                
                # Wait for venue tiles to load - try multiple selectors
                print("  Waiting for venue listings to load...")
                try:
                    page.wait_for_selector("[data-test-id='storefrontTitle']", timeout=15000)
                except:
                    try:
                        page.wait_for_selector(".vendorTile__title", timeout=10000)
                    except:
                        try:
                            page.wait_for_selector(".vendorTile", timeout=10000)
                        except:
                            print("  Warning: Could not detect venue elements, trying anyway...")
                
                # Scroll down to trigger lazy loading
                print("  Scrolling to load all content...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(2)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Get total pages (for information only - we'll use has_next_page for control)
                html = page.content()
                total_pages = get_total_pages_from_html(html)
                print(f"Detected approximately {total_pages} page(s) of venues")
                
                # === IMPROVED PAGINATION LOGIC ===
                current_page = 1
                max_pages = 100  # Safety limit to prevent infinite loops
                seen_venue_urls = set()  # Track ALL venues seen to avoid duplicates
                consecutive_no_new = 0  # Track consecutive pages with no new venues
                
                # Scrape page 1 first (we're already on it)
                print(f"\nScraping page {current_page}...", end=" ")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(1)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                html = page.content()
                page_venues = extract_venues_from_html(html)
                
                # Add only new venues
                new_count = 0
                for venue in page_venues:
                    if venue[1] not in seen_venue_urls:
                        all_venues.append(venue)
                        seen_venue_urls.add(venue[1])
                        new_count += 1
                
                print(f"Found {len(page_venues)} venues ({new_count} new)")
                
                # Continue scraping while there's a next page button available
                while current_page < max_pages:
                    # Check if next button exists and is enabled BEFORE clicking
                    print(f"\n  Checking for next page...", end=" ")
                    if not has_next_page(page):
                        print("No more pages (next button disabled or not found)")
                        break
                    print("found!")
                    
                    next_page_num = current_page + 1
                    
                    # Step 1: Click next to go to the next page
                    print(f"  Clicking next to go to page {next_page_num}...")
                    
                    # Store current URL and venue count to detect navigation
                    current_url = page.url
                    expected_venue_count = len(page_venues)  # Expect similar count to previous page
                    
                    if not click_next_page(page):
                        print(f"  Could not click next button - stopping")
                        break
                    
                    # Step 2: Wait for content to load and verify page changed
                    print(f"  Waiting for new content...", end=" ", flush=True)
                    time.sleep(3)  # Longer initial wait after click
                    
                    # Wait for new content - need BOTH new venues AND a reasonable count
                    max_wait_attempts = 60  # Increased attempts
                    page_loaded = False
                    best_venue_count = 0
                    best_new_count = 0
                    
                    for wait_attempt in range(max_wait_attempts):
                        # Scroll to trigger lazy loading on each check
                        if wait_attempt % 5 == 0:
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                            time.sleep(0.3)
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        
                        # Get current page content
                        html_check = page.content()
                        check_venues = extract_venues_from_html(html_check)
                        
                        if check_venues and len(check_venues) > 0:
                            # Count how many are new (not seen before)
                            current_urls = set(url for _, url in check_venues)
                            new_urls = current_urls - seen_venue_urls
                            
                            # Track the best result we've seen
                            if len(new_urls) > best_new_count:
                                best_new_count = len(new_urls)
                                best_venue_count = len(check_venues)
                            
                            # Success criteria: 
                            # - Have new venues AND
                            # - Either have a good count (>20) OR count has stabilized
                            if len(new_urls) > 0:
                                # If we have a lot of new venues, we're good
                                if len(new_urls) >= 20:
                                    page_loaded = True
                                    print(f"OK ({len(check_venues)} venues, {len(new_urls)} new)")
                                    break
                                # If we have fewer but count seems stable (waited long enough)
                                elif wait_attempt >= 20 and len(check_venues) >= best_venue_count:
                                    page_loaded = True
                                    print(f"OK ({len(check_venues)} venues, {len(new_urls)} new)")
                                    break
                        
                        if wait_attempt % 15 == 14:
                            print(".", end="", flush=True)
                        time.sleep(0.5)
                    
                    if not page_loaded:
                        # One more aggressive attempt - scroll fully and wait
                        print(f" retrying...", end="", flush=True)
                        page.evaluate("window.scrollTo(0, 0)")
                        time.sleep(1)
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(3)
                        
                        html_check = page.content()
                        check_venues = extract_venues_from_html(html_check)
                        if check_venues:
                            current_urls = set(url for _, url in check_venues)
                            new_urls = current_urls - seen_venue_urls
                            if len(new_urls) > 0:
                                page_loaded = True
                                print(f" recovered ({len(check_venues)} venues, {len(new_urls)} new)")
                        
                        if not page_loaded:
                            print(f"\n  Warning: Page may not have fully loaded (best: {best_venue_count} venues, {best_new_count} new)")
                    
                    # Update current_page
                    current_page = next_page_num
                    
                    # Step 3: Scroll thoroughly to ensure all lazy-loaded content appears
                    # Scroll in stages to trigger all lazy loading
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.5)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.25)")
                    time.sleep(0.5)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
                    time.sleep(0.5)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.75)")
                    time.sleep(0.5)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)  # Longer wait at bottom for lazy loading
                    
                    # Scroll back up and down once more to catch anything missed
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.5)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    # Step 4: Extract venues from this page
                    html = page.content()
                    page_venues = extract_venues_from_html(html)
                    
                    if not page_venues:
                        print(f"  Warning: No venues found on page {current_page}")
                        consecutive_no_new += 1
                        if consecutive_no_new >= 2:
                            print(f"  Stopping: {consecutive_no_new} consecutive pages with no venues")
                            break
                        continue
                    
                    # Add only new venues (avoid duplicates)
                    new_count = 0
                    for venue in page_venues:
                        if venue[1] not in seen_venue_urls:
                            all_venues.append(venue)
                            seen_venue_urls.add(venue[1])
                            new_count += 1
                    
                    print(f"  Page {current_page}: Found {len(page_venues)} venues, added {new_count} new (total: {len(all_venues)})")
                    
                    if new_count == 0:
                        consecutive_no_new += 1
                        if consecutive_no_new >= 2:
                            print(f"  Stopping: {consecutive_no_new} consecutive pages with no new venues")
                            break
                    else:
                        consecutive_no_new = 0
                    
                    # Small delay to be polite to the server
                    time.sleep(0.5)
                
                print(f"\n  Pagination complete. Scraped {current_page} pages.")
                
            except Exception as e:
                print(f"Error during scraping: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                browser.close()
                print("Browser closed")
                
    except Exception as e:
        print(f"\nError launching browser: {e}")
        print("\nTroubleshooting steps:")
        print("  1. Run: pip install playwright")
        print("  2. Run: playwright install chromium")
        print("  3. Try again")
    
    return all_venues


def save_to_csv(venues, filename):
    """Save venues to a CSV file."""
    # Check if venues have email data (3 columns) or not (2 columns)
    has_emails = len(venues[0]) == 3 if venues else False
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if has_emails:
            writer.writerow(["Venue Name", "URL", "Email"])
        else:
            writer.writerow(["Venue Name", "URL"])
        writer.writerows(venues)
    print(f"\nResults saved to: {filename}")


def extract_emails_from_html(html):
    """Extract email addresses from HTML content."""
    emails = set()
    
    # Find all email patterns in the HTML
    found_emails = EMAIL_PATTERN.findall(html)
    
    for email in found_emails:
        # Filter out common false positives
        email_lower = email.lower()
        if not any(skip in email_lower for skip in [
            'example.com', 'domain.com', 'email.com', 'test.com',
            'yourname@', 'name@', '.png', '.jpg', '.gif', '.svg',
            'webpack', 'node_modules', 'sentry'
        ]):
            emails.add(email.lower())
    
    return list(emails)


def scrape_venue_emails(venues, max_venues=None):
    """
    Visit each venue's Hitched page and extract email addresses.
    
    Args:
        venues: List of tuples (venue_name, venue_url)
        max_venues: Maximum number of venues to process (None for all)
        
    Returns:
        List of tuples (venue_name, venue_url, email)
    """
    results = []
    total = len(venues) if max_venues is None else min(len(venues), max_venues)
    
    print(f"\nExtracting emails from {total} venue pages...")
    print("This may take a while. The browser will visit each page.\n")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-GB",
                timezone_id="Europe/London",
            )
            
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            for i, (name, url) in enumerate(venues[:total]):
                print(f"[{i+1}/{total}] {name}...", end=" ", flush=True)
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)  # Let page load
                    
                    html = page.content()
                    emails = extract_emails_from_html(html)
                    
                    if emails:
                        email_str = "; ".join(emails)
                        print(f"Found: {email_str}")
                        results.append((name, url, email_str))
                    else:
                        print("No email found")
                        results.append((name, url, ""))
                    
                    # Small delay between requests
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error: {e}")
                    results.append((name, url, ""))
            
            browser.close()
            
    except Exception as e:
        print(f"Browser error: {e}")
    
    # Count results
    found = sum(1 for _, _, email in results if email)
    print(f"\nEmail extraction complete: Found emails for {found}/{total} venues")
    
    return results


def print_venues(venues):
    """Display venues in a formatted table."""
    print("\n" + "=" * 100)
    print(f"{'#':<5} {'VENUE NAME':<50} | URL")
    print("=" * 100)
    for i, (name, url) in enumerate(venues, 1):
        display_name = name[:47] + "..." if len(name) > 50 else name
        print(f"{i:<5} {display_name:<50} | {url}")
    print("=" * 100)


def main():
    """Main function to run the scraper."""
    print("\n" + "*" * 60)
    print("*" + " " * 58 + "*")
    print("*   HITCHED.CO.UK WEDDING VENUE SCRAPER                    *")
    print("*   Powered by Playwright (handles anti-bot protection)    *")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    
    while True:
        display_menu()
        choice = get_user_choice()
        
        if choice is None:
            print("\nThank you for using the Hitched Venue Scraper. Goodbye!")
            break
        
        region_name, region_slug = REGIONS[choice]
        print(f"\nYou selected: {region_name}")
        print("-" * 40)
        
        # Scrape venues
        venues = scrape_region(region_slug, region_name)
        
        if not venues:
            print("\nNo venues found or an error occurred.")
            continue
        
        # Remove duplicates while preserving order (should already be handled, but double-check)
        seen = set()
        unique_venues = []
        for venue in venues:
            if venue[1] not in seen:
                seen.add(venue[1])
                unique_venues.append(venue)
        
        print(f"\n{'=' * 50}")
        print(f"SCRAPING COMPLETE!")
        print(f"{'=' * 50}")
        print(f"Total unique venues found: {len(unique_venues)}")
        
        # Ask user what to do with results
        print("\nWhat would you like to do with the results?")
        print("  [1] Display in terminal")
        print("  [2] Save to CSV file")
        print("  [3] Both")
        print("  [4] Skip")
        
        action = input("\nEnter choice (1-4): ").strip()
        
        if action in ["1", "3"]:
            print_venues(unique_venues)
        
        if action in ["2", "3"]:
            safe_region = region_slug.replace("-", "_")
            filename = f"hitched_venues_{safe_region}.csv"
            save_to_csv(unique_venues, filename)
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
