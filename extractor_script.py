import time
import json
import os
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

def extract_facebook_image_urls(post_url, driver, use_login=False):
    """Extract image URLs from a single Facebook post with optimized timeouts"""
    
    timeout = 15
    short_wait = 2
    page_load_wait = 3
    
    try:
        # Navigate to the post URL
        print(f"Navigating to: {post_url}")
        driver.get(post_url)
        time.sleep(page_load_wait)  # Reduced wait time
        
        # First get the visible image links as a fallback (faster approach)
        visible_image_links = []
        try:
            print("Getting visible image links...")
            # Combined XPath for efficiency
            combined_xpath = "//a[contains(@href, '/photo/?fbid=')] | //a[contains(@href, '/photo?fbid=')] | //a[contains(@href, 'set=pcb.')] | //div[@role='article']//a[.//img]"
            elements = driver.find_elements(By.XPATH, combined_xpath)
            
            for element in elements:
                link = element.get_attribute('href')
                if link and link not in visible_image_links and ('fbid=' in link or 'photo' in link):
                    visible_image_links.append(link)
            
            print(f"Found {len(visible_image_links)} visible image links")
            
            # If we have enough links already, return them without trying to open the viewer
            if len(visible_image_links) >= 5:
                print("Found sufficient links without photo viewer, skipping viewer navigation")
                return clean_links(visible_image_links)
                
        except Exception as e:
            print(f"Error finding visible image links: {str(e)}")
        
        # Primary approach: Click on the first image and navigate through all photos
        image_links = []
        viewer_opened = False
        
        try:
            print("Looking for clickable images...")
            
            # Optimized selector strategy - try most reliable ones first
            clickable_selectors = [
                "//a[contains(@href, '/photo')]//img",
                "//div[@role='article']//img[not(contains(@src, 'emoji')) and not(contains(@src, 'icon'))]"
            ]
            
            for selector in clickable_selectors:
                try:
                    images = driver.find_elements(By.XPATH, selector)
                    
                    if images:
                        print(f"Found {len(images)} potential clickable images")
                        # Try each image until one opens the viewer
                        for i, img in enumerate(images[:3]):  # Try only first 3 images
                            try:
                                print(f"Attempting to click image {i+1}...")
                                driver.execute_script("arguments[0].scrollIntoView(true);", img)
                                driver.execute_script("arguments[0].click();", img)  # Using JS click for reliability
                                time.sleep(short_wait)
                                
                                # Check if we're in a photo viewer - simplified check
                                current_url = driver.current_url
                                if 'photo' in current_url and 'fbid=' in current_url:
                                    print("Photo viewer detected through URL")
                                    viewer_opened = True
                                    break
                                else:
                                    print("Click did not open photo viewer, trying to go back...")
                                    driver.back()
                                    time.sleep(1)  # Reduced wait time
                            except Exception as e:
                                print(f"Error clicking image {i+1}: {str(e)}")
                                try:
                                    driver.back()
                                    time.sleep(1)
                                except:
                                    pass
                                
                        if viewer_opened:
                            break
                except Exception as e:
                    print(f"Error with selector {selector}: {str(e)}")
            
            # If we successfully opened the viewer, extract all images
            if viewer_opened:
                print("Navigating through photos in the viewer...")
                
                # Record the first image URL
                current_url = driver.current_url
                if 'fbid=' in current_url and current_url not in image_links:
                    image_links.append(current_url)
                    print(f"Added image 1: {current_url}")
                
                # Navigate through photos with optimized parameters
                photo_count = 1
                max_attempts = 15  # Reduced maximum 
                consecutive_failures = 0
                
                while photo_count < max_attempts and consecutive_failures < 2:  # Reduced threshold
                    try:
                        # Optimized next button finding - use JS to find and click
                        js_script = """
                        var nextButtons = document.querySelectorAll('[aria-label="Next photo"], [data-testid="chevron-right-overlay"]');
                        if (nextButtons.length > 0) {
                            nextButtons[0].click();
                            return true;
                        }
                        return false;
                        """
                        clicked = driver.execute_script(js_script)
                        
                        if clicked:
                            time.sleep(1)  # Reduced wait
                            
                            # Get the URL of this photo
                            current_url = driver.current_url
                            if 'fbid=' in current_url and current_url not in image_links:
                                image_links.append(current_url)
                                photo_count += 1
                                consecutive_failures = 0
                                print(f"Added image {photo_count}: {current_url}")
                            else:
                                consecutive_failures += 1
                        else:
                            consecutive_failures += 1
                            print("Next button not found, may have reached the end")
                            
                    except Exception as e:
                        consecutive_failures += 1
                        print(f"Error navigating to next photo: {str(e)}")
                    
                    # If failures, we've probably reached the end
                    if consecutive_failures >= 2:
                        print("Navigation failures, ending photo viewer navigation")
                        break
                
                print(f"Found total of {len(image_links)} images through photo viewer")
                
                # Return to the post page - simplified navigation
                driver.get(post_url)
                time.sleep(short_wait)
            
        except Exception as e:
            print(f"Error in photo viewer navigation: {str(e)}")
        
        # If photo viewer approach failed, use the fallback visible links
        if not image_links and visible_image_links:
            print("Using fallback visible image links")
            image_links = visible_image_links
        
        return clean_links(image_links)
            
    except Exception as e:
        print(f"An error occurred processing {post_url}: {str(e)}")
        return []

def clean_links(image_links):
    """Clean URLs by stripping tracking parameters while keeping essential fbid"""
    cleaned_links = []
    for url in image_links:
        try:
            # Extract the essential parts (fbid and set parameters)
            if 'fbid=' in url and 'set=' in url:
                # Find fbid parameter
                fbid_start = url.find('fbid=')
                fbid_end = url.find('&', fbid_start)
                if fbid_end == -1:
                    fbid_end = len(url)
                fbid_param = url[fbid_start:fbid_end]
                
                # Find set parameter
                set_start = url.find('set=')
                set_end = url.find('&', set_start)
                if set_end == -1:
                    set_end = len(url)
                set_param = url[set_start:set_end]
                
                # Create clean URL
                clean_url = f"https://www.facebook.com/photo?{fbid_param}&{set_param}"
                if clean_url not in cleaned_links:
                    cleaned_links.append(clean_url)
            else:
                # Just keep the original URL if we can't parse it properly
                if url not in cleaned_links:
                    cleaned_links.append(url)
        except Exception as e:
            print(f"Error cleaning URL {url}: {str(e)}")
            if url not in cleaned_links:
                cleaned_links.append(url)
    
    return cleaned_links

def setup_driver(headless=False):
    """Set up and return a configured Chrome driver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--dns-prefetch-disable")
    
    # Add performance preferences
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # Do not load images
            'plugins': 2,  # Do not load plugins
            'popups': 2,  # Block popups
            'geolocation': 2,  # Block geolocation
            'notifications': 2  # Block notifications
        },
        'disk-cache-size': 4096,
        'media.autoplay.enabled': False
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    return webdriver.Chrome(options=chrome_options)

def process_multiple_posts_parallel(urls, use_login, email=None, password=None, headless=True, max_workers=3):
    """Process multiple URLs in parallel using a thread pool"""
    all_results = {}
    
    # Create a pool of workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a driver for each worker
        drivers = []
        for _ in range(max_workers):
            driver = setup_driver(headless)
            drivers.append(driver)
            
            # Login if required (only needed once per driver)
            if use_login and email and password:
                try:
                    login_to_facebook(driver, email, password)
                except Exception as e:
                    print(f"Login failed: {str(e)}")
        
        # Submit tasks
        future_to_url = {}
        for i, url in enumerate(urls):
            # Use round-robin assignment of drivers
            driver_index = i % len(drivers)
            future = executor.submit(extract_facebook_image_urls, url, drivers[driver_index], use_login)
            future_to_url[future] = url
        
        # Process completed tasks
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                image_urls = future.result()
                print(f"\n[{i+1}/{len(urls)}] Completed: {url}")
                
                if image_urls:
                    print(f"Found {len(image_urls)} images for this post")
                    all_results[url] = image_urls
                else:
                    print("No images found for this post")
                    all_results[url] = []
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                all_results[url] = []
    
    # Close all drivers
    for driver in drivers:
        try:
            driver.quit()
        except:
            pass
            
    return all_results

def login_to_facebook(driver, email, password):
    """Login to Facebook with the given credentials"""
    print("Logging into Facebook...")
    driver.get("https://www.facebook.com/")
    
    # Accept cookies if prompted
    try:
        cookie_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(string(), 'Allow') or contains(string(), 'Accept')]"))
        )
        cookie_button.click()
    except TimeoutException:
        pass
        
    # Enter email
    email_field = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "email"))
    )
    email_field.send_keys(email)
    
    # Enter password
    password_field = driver.find_element(By.ID, "pass")
    password_field.send_keys(password)
    
    # Click login
    login_button = driver.find_element(By.NAME, "login")
    login_button.click()
    
    # Wait for login to complete
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='navigation']"))
        )
        print("Login successful")
    except TimeoutException:
        print("Login may have failed or page structure has changed. Continuing anyway...")

def process_multiple_posts():
    print("Facebook Image URL Extractor (Multiple Posts - Optimized)")
    print("-----------------------------------------------------")
    
    # Get input method
    input_method = input("Choose input method:\n1. Enter single URL\n2. Load URLs from file\nEnter choice (1/2): ")
    
    post_urls = []
    
    if input_method == "1":
        url = input("Enter the Facebook post URL: ")
        post_urls.append(url)
    elif input_method == "2":
        file_path = input("Enter the path to the text file containing Facebook post URLs: ")
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    url = line.strip()
                    if url and url.startswith('http'):
                        post_urls.append(url)
            print(f"Loaded {len(post_urls)} URLs from file")
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            return
    else:
        print("Invalid choice. Please run the script again.")
        return
    
    if not post_urls:
        print("No valid URLs found. Exiting.")
        return
    
    # Ask if user wants to login
    use_login = input("Do you want to login to Facebook? (y/n): ").lower() == 'y'
    
    email = None
    password = None
    if use_login:
        email = input("Enter your Facebook email: ")
        password = input("Enter your Facebook password: ")
    
    # Ask if headless mode is preferred
    headless = input("Run in headless mode (no visible browser)? (y/n): ").lower() == 'y'
    
    # Ask for parallel processing
    parallel = input("Use parallel processing (faster but uses more memory)? (y/n): ").lower() == 'y'
    
    max_workers = 1
    if parallel:
        try:
            max_workers = int(input(f"Enter number of parallel browsers (1-5, recommended 2-3): "))
            max_workers = max(1, min(5, max_workers))  # Limit between 1 and 5
        except:
            max_workers = 2  # Default if invalid input
    
    # Process URLs
    all_results = {}
    start_time = time.time()
    
    if parallel and len(post_urls) > 1:
        print(f"Starting parallel processing with {max_workers} workers...")
        all_results = process_multiple_posts_parallel(post_urls, use_login, email, password, headless, max_workers)
    else:
        print("Starting sequential processing...")
        driver = setup_driver(headless)
        
        try:
            # Login if credentials provided
            if use_login and email and password:
                login_to_facebook(driver, email, password)
            else:
                print("Proceeding without login. Some content may not be accessible.")
            
            # Process each URL sequentially
            for i, url in enumerate(post_urls):
                print(f"\n[{i+1}/{len(post_urls)}] Processing: {url}")
                image_urls = extract_facebook_image_urls(url, driver, use_login)
                
                if image_urls:
                    print(f"Found {len(image_urls)} images for this post")
                    all_results[url] = image_urls
                else:
                    print("No images found for this post")
                    all_results[url] = []
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            
        finally:
            # Close the browser
            print("Closing browser...")
            driver.quit()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Output results
    total_images = sum(len(urls) for urls in all_results.values())
    print(f"\nProcessed {len(post_urls)} posts and found {total_images} images in total")
    print(f"Total processing time: {elapsed_time:.2f} seconds")
    
    # Ask to save to file
    if total_images > 0:
        save_to_file = input("\nSave URLs to a file? (y/n): ").lower() == 'y'
        if save_to_file:
            filename = input("Enter filename (default: image_urls.json): ") or "image_urls.json"
            
            # Save in JSON format with post URLs as keys and image URLs as values
            with open(filename, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"Saved {total_images} URLs from {len(all_results)} posts to {filename}")
            
            # Also save as a simple text file with one URL per line if requested
            save_text = input("Also save as simple text file (one URL per line)? (y/n): ").lower() == 'y'
            if save_text:
                text_filename = os.path.splitext(filename)[0] + ".txt"
                with open(text_filename, 'w') as f:
                    for post_url, image_urls in all_results.items():
                        f.write(f"# Post: {post_url}\n")
                        for url in image_urls:
                            f.write(f"{url}\n")
                        f.write("\n")
                print(f"Saved as text to {text_filename}")

# Run the function directly
if __name__ == "__main__":
    process_multiple_posts()
    
    # Keep the console open if run directly
    input("\nPress Enter to exit...")