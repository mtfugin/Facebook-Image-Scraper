# Facebook Image Scraper
![image](https://github.com/user-attachments/assets/becf7c12-8484-4f01-8cdc-1eedc08afd97)


These two Python scripts collaborate to extract image URLs from Facebook posts and download the corresponding images to your local machine.

## Overview
- **Facebook Image URL Extractor:** This script uses Selenium to navigate through specified Facebook posts and extract the URLs of images embedded in those posts. It supports extracting from single or multiple posts, offers optional login for accessing private content, and includes parallel processing for efficiency. The extracted URLs are saved to a JSON file.
- **Facebook Image Scraper:** This script takes the JSON file generated by the extractor and downloads the images to a specified local folder. It leverages requests and BeautifulSoup for fetching and parsing web content, with parallel downloads to improve speed.

## Prerequisites

Before using the scripts, ensure you have the following installed:

- Python 3.x: The scripts are written in Python 3.
- Google Chrome: Required for the extractor script, as it uses Selenium with ChromeDriver.
- ChromeDriver: Must match your Chrome browser version. Download it from [here](https://sites.google.com/chromium.org/driver/) and add it to your system's PATH.

**Or Install Chrome + ChromeDriver using Terminal**
- `wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb`
- `sudo apt install -y ./google-chrome-stable_current_amd64.deb`
- `pip install webdriver-manager`

### Required Python Libraries
The following libraries are necessary to run both scripts:

- **selenium**: Used in the Facebook Image URL Extractor for browser automation with Selenium WebDriver.
- **requests**: Used in the Facebook Image Scraper to make HTTP requests and fetch web content.
- **beautifulsoup4**: Used in the Facebook Image Scraper for parsing HTML content (imported as BeautifulSoup from the bs4 module).
- **tqdm**: Used in the Facebook Image Scraper to display a progress bar during execution.

Both scripts also use several standard Python libraries (e.g., os, time, json, re, threading, concurrent.futures), but these come pre-installed with Python 3.x and do not require separate installation.

### Installation Instructions
You can install all the required libraries using `pip`, the Python package manager. Assuming you have Python 3.x installed, open a terminal or command prompt and run the following command to install all four libraries at once:

- `pip install selenium requests beautifulsoup4 tqdm`

### Additional Notes on Installation
- **Python Version:** Ensure you have Python 3.x installed, as these libraries are compatible with Python 3.
- **Selenium WebDriver:** The Facebook Image URL Extractor uses Selenium with a WebDriver (e.g., ChromeDriver for Google Chrome). While selenium is the Python library, you also need to:
  - Install Google Chrome on your system.
  - Download the appropriate version of ChromeDriver matching your Chrome version and add it to your system's PATH. Alternatively, you can use the optional **webdriver-manager** library to automate this process by running `pip install webdriver-manager`, but this is not required for the basic script.


## Usage
### Facebook Image URL Extractor
This script extracts image URLs from Facebook posts and saves them to a JSON file.

#### 1. Run the Script: 
`python extractor_script.py`
#### 2. Choose Input Method:
- Enter `1` to input a single Facebook post URL manually.
- Enter `2` to load multiple URLs from a text file (one URL per line).
#### 3. Provide Input:
- If you chose 2, enter the path to your text file (e.g., `posts.txt`).
#### 4. Login Option:
- Enter `y` to log in to Facebook (required for private posts).
- Enter `n` to proceed without logging in.
#### 5. Login Credentials (if applicable):
- Provide your Facebook email and password when prompted.
#### 6. Headless Mode:
- Enter `y` to run in headless mode (no visible browser window).
- Enter `n` to see the browser during execution.
#### 7. Parallel Processing (for multiple URLs):
Enter `y` to use parallel processing (faster but resource-intensive).
Enter `n` for sequential processing.
#### 8. Number of Browsers (if parallel):
- Specify the number of parallel browsers (1-5).
#### 9. Processing:
- The script will navigate the posts and extract image URLs.
#### 10. Save Results:
- After extraction, choose whether to save the URLs to a JSON file (y or n).
If `y`, provide a filename (e.g., `image_urls.json`) or press Enter for the default.

### Facebook Image Scraper
This script downloads images from the URLs saved in the JSON file.

#### 1. Run the Script:
`python scraper_script.py`
#### 2. Input JSON File:
Enter the path to the JSON file generated by the extractor (e.g., `image_urls.json`).
#### 3. Output Folder:
Enter the path to the folder where images will be saved (e.g., `downloaded_images`). The folder will be created if it doesn’t exist.
#### 4. Download Process:
The script will download the images, displaying a progress bar with `tqdm`.
#### 5. Completion:
A summary will show the number of images successfully downloaded.

### Authentication for Scraper Script
To download images from private posts, the scraper script can use Facebook cookies for authentication. Here’s how to set it up:

#### Option 1: Environment Variables:
Set the following environment variables with your cookie values:
- `FB_C_USER`: Your `c_user` cookie.
- `FB_XS`: Your `xs` cookie.
- Option 2: Cookies File:
Create a `cookies.json`file in  the same directory as the script with this format:

    {
    "c_user": "your_c_user_value",
    "xs": "your_xs_value"
    }
- The script will load cookies from this file if it exists; otherwise, it falls back to environment variables.

**How to Obtain Cookies:**

    1. Log in to Facebook in your browser.
    2. Open developer tools (F12), go to the "Network" tab, and refresh the page.
    3. Find a request to facebook.com, locate the cookie header, and copy the c_user and xs values.

## Disclaimer
These scripts are provided for educational purposes only.
Scraping Facebook may violate their Terms of Service. Use at your own risk.
The author is not responsible for any consequences arising from the use of these scripts.

## MIT License
©️ 2025 Amerogin Kamid

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
