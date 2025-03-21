import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import django
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, Category
from django.conf import settings

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def download_image(url, save_path, size=(800, 800)):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.convert('RGB')
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(save_path, 'JPEG', quality=85)
            return True
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
    return False

def get_image_urls(query, driver, num_images=1):
    try:
        # Search for images on Google
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        driver.get(search_url)
        time.sleep(2)  # Wait for images to load
        
        # Scroll to load more images
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Get image elements
        images = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
        image_urls = []
        
        for img in images[:num_images]:
            try:
                img.click()
                time.sleep(1)
                
                # Wait for the large image to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.r48jcc"))
                )
                
                # Get the large image URL
                large_img = driver.find_element(By.CSS_SELECTOR, "img.r48jcc")
                image_urls.append(large_img.get_attribute('src'))
            except:
                continue
                
        return image_urls
    except Exception as e:
        print(f"Error getting image URLs for {query}: {str(e)}")
        return []

def process_products():
    driver = setup_driver()
    media_root = settings.MEDIA_ROOT
    
    # Create necessary directories
    os.makedirs(os.path.join(media_root, 'products'), exist_ok=True)
    os.makedirs(os.path.join(media_root, 'categories'), exist_ok=True)
    
    # Process products
    products = Product.objects.all()
    for product in products:
        if not product.images.exists():
            print(f"Processing product: {product.name}")
            image_urls = get_image_urls(f"{product.name} product", driver)
            
            if image_urls:
                image_path = os.path.join(media_root, 'products', f"{product.id}.jpg")
                if download_image(image_urls[0], image_path):
                    product.images.create(image=f'products/{product.id}.jpg')
                    print(f"Added image for {product.name}")
            
            time.sleep(2)  # Delay between products
    
    # Process categories
    categories = Category.objects.all()
    for category in categories:
        if not category.image:
            print(f"Processing category: {category.name}")
            image_urls = get_image_urls(f"{category.name} category banner", driver)
            
            if image_urls:
                image_path = os.path.join(media_root, 'categories', f"{category.id}.jpg")
                if download_image(image_urls[0], image_path, size=(800, 400)):
                    category.image = f'categories/{category.id}.jpg'
                    category.save()
                    print(f"Added image for {category.name}")
            
            time.sleep(2)  # Delay between categories
    
    driver.quit()

if __name__ == '__main__':
    process_products() 