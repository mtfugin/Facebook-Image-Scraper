import requests
from bs4 import BeautifulSoup
import os
import time
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading

# Configuration
DISPLAY_IMAGES = False  # Image preview disabled

# Lock for thread-safe progress bar updates
pbar_lock = threading.Lock()

def download_image(session, url, output_folder, index, total, pbar):
    """Download an image from a URL and save it to the specified folder."""
    try:
        # Generate a filename based on post ID or timestamp
        post_id = re.search(r'fbid=(\d+)', url)
        if post_id:
            filename = f"fb_{post_id.group(1)}_{index}.jpg"
        else:
            filename = f"facebook_image_{int(time.time())}_{index}.jpg"
        
        file_path = os.path.join(output_folder, filename)
        
        # Log the download start
        with pbar_lock:
            pbar.write(f"Downloading image {index}/{total}: {filename}")
        
        # Download the image
        img_response = session.get(url, stream=True)
        img_response.raise_for_status()
        
        # Skip small images (e.g., icons)
        content_length = int(img_response.headers.get('Content-Length', 0))
        if content_length < 10000:
            with pbar_lock:
                pbar.write(f"Skipping small image (size: {content_length} bytes)")
            return None
        
        # Save the image to disk
        with open(file_path, 'wb') as f:
            for chunk in img_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        with pbar_lock:
            pbar.write(f"✓ Successfully downloaded: {filename}")
        
        return file_path
    
    except Exception as e:
        with pbar_lock:
            pbar.write(f"Error downloading image: {e}")
        return None

def process_facebook_link(session, url, pbar):
    """Process a single Facebook link and extract image URLs."""
    try:
        with pbar_lock:
            pbar.write(f"\nFetching post: {url}")
        
        # Fetch the page content
        response = session.get(url, allow_redirects=True)
        response.raise_for_status()
        
        # Check for login redirect
        if '/login/' in response.url:
            with pbar_lock:
                pbar.write("⚠️ Redirected to login page. Authentication required.")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for images with specific attributes
        images = soup.find_all('img', attrs={'data-visualcompletion': 'media-vc-image'})
        
        if not images:
            with pbar_lock:
                pbar.write("No images found with data-visualcompletion='media-vc-image'")
                pbar.write("Trying alternative method...")
            # Fallback to regex pattern matching
            image_pattern = r'https:\/\/scontent[^"\']+\.(?:jpg|jpeg|png|gif)'
            image_urls = re.findall(image_pattern, response.text)
            
            if image_urls:
                with pbar_lock:
                    pbar.write(f"Found {len(image_urls)} image URLs using pattern matching")
                image_urls = list(dict.fromkeys(image_urls))  # Remove duplicates
                images = []
                for img_url in image_urls:
                    fake_img = soup.new_tag('img')
                    fake_img['src'] = img_url
                    images.append(fake_img)
            else:
                images = soup.find_all('img')
                with pbar_lock:
                    pbar.write(f"Found {len(images)} other images on the page")
        else:
            with pbar_lock:
                pbar.write(f"Found {len(images)} images with data-visualcompletion='media-vc-image'")
        
        # Extract and filter image URLs
        image_urls = []
        for img in images:
            if 'src' in img.attrs:
                src = img['src']
                clean_url = src.replace('&', '&')  # Ensure URL integrity
                if 'icon' in clean_url.lower() or 'logo' in clean_url.lower():
                    continue
                image_urls.append(clean_url)
        
        return image_urls
    
    except Exception as e:
        with pbar_lock:
            pbar.write(f"Error processing URL {url}: {e}")
        return []

def process_photo_link(session, photo_link, output_folder, pbar):
    """Process a single photo link and download its images."""
    # Skip non-photo or download links
    if "download" in photo_link or "pcb" not in photo_link:
        with pbar_lock:
            pbar.write(f"Skipping non-photo link: {photo_link}")
        return []
    
    # Get image URLs from the photo link
    image_urls = process_facebook_link(session, photo_link, pbar)
    downloaded_files = []
    
    # Download each image
    for j, img_url in enumerate(image_urls):
        file_path = download_image(session, img_url, output_folder, j+1, len(image_urls), pbar)
        if file_path:
            downloaded_files.append(file_path)
    
    return downloaded_files

def main():
    """Main function to process JSON file and download images in parallel."""
    # User input
    json_file_path = input("Enter the path to the JSON file: ")
    output_folder = input("Enter the output folder path: ")
    
    # Ensure output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")
    else:
        print(f"Using existing output directory: {output_folder}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.facebook.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    if cookies['c_user'] and cookies['xs']:
        print("Using provided authentication cookies")
        for cookie_name, cookie_value in cookies.items():
            session.cookies.set(cookie_name, cookie_value, domain='.facebook.com')
    else:
        print("⚠️ No authentication cookies provided. Facebook may require login.")
    
    try:
        # Load JSON file
        print(f"Loading JSON file: {json_file_path}")
        with open(json_file_path, 'r') as f:
            facebook_links = json.load(f)
        
        # Collect all valid photo links for parallel processing
        all_photo_links = []
        for post_url, photo_links in facebook_links.items():
            for photo_link in photo_links:
                if "pcb" in photo_link and "download" not in photo_link:
                    all_photo_links.append(photo_link)
        
        total_photo_links = len(all_photo_links)
        all_downloaded_files = []
        
        # Process photo links in parallel
        with tqdm(total=total_photo_links, desc="Processing photo links") as pbar:
            with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
                future_to_photo_link = {
                    executor.submit(process_photo_link, session, photo_link, output_folder, pbar): photo_link
                    for photo_link in all_photo_links
                }
                
                for future in as_completed(future_to_photo_link):
                    try:
                        downloaded_files = future.result()
                        all_downloaded_files.extend(downloaded_files)
                    except Exception as e:
                        with pbar_lock:
                            pbar.write(f"Error processing photo link: {e}")
                    finally:
                        pbar.update(1)
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"DOWNLOAD SUMMARY")
        print(f"{'='*80}")
        print(f"Processed {len(facebook_links)} posts with {total_photo_links} photo links")
        print(f"Successfully downloaded {len(all_downloaded_files)} images to {output_folder}")
        
        if all_downloaded_files:
            print("\nDownloaded files:")
            for file in all_downloaded_files:
                print(f"- {file}")
        else:
            print("\n❌ No images were downloaded.")
    
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: '{json_file_path}' is not a valid JSON file.")
    except Exception as e:
        print(f"Error in main function: {e}")

if __name__ == "__main__":
    main()

