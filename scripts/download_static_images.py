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
from PIL import Image
from io import BytesIO

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def download_image(url, save_path, size=None):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.convert('RGB')
            if size:
                img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(save_path, quality=85)
            return True
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
    return False

def get_image_urls(query, driver, num_images=1):
    try:
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        driver.get(search_url)
        time.sleep(2)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        images = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
        image_urls = []
        
        for img in images[:num_images]:
            try:
                img.click()
                time.sleep(1)
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.r48jcc"))
                )
                
                large_img = driver.find_element(By.CSS_SELECTOR, "img.r48jcc")
                image_urls.append(large_img.get_attribute('src'))
            except:
                continue
                
        return image_urls
    except Exception as e:
        print(f"Error getting image URLs for {query}: {str(e)}")
        return []

def download_static_images():
    driver = setup_driver()
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    images_dir = os.path.join(static_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # Download logo
    print("Downloading logo...")
    logo_urls = get_image_urls("modern ecommerce logo design", driver)
    if logo_urls:
        logo_path = os.path.join(images_dir, 'logo.png')
        if download_image(logo_urls[0], logo_path, size=(200, 50)):
            print("Logo downloaded successfully")
    
    # Download hero images
    print("Downloading hero images...")
    hero1_urls = get_image_urls("modern ecommerce hero banner 1", driver)
    if hero1_urls:
        hero1_path = os.path.join(images_dir, 'hero1.jpg')
        if download_image(hero1_urls[0], hero1_path, size=(1920, 500)):
            print("Hero 1 downloaded successfully")
    
    hero2_urls = get_image_urls("modern ecommerce hero banner 2", driver)
    if hero2_urls:
        hero2_path = os.path.join(images_dir, 'hero2.jpg')
        if download_image(hero2_urls[0], hero2_path, size=(1920, 500)):
            print("Hero 2 downloaded successfully")
    
    # Download default images
    print("Downloading default images...")
    no_image_urls = get_image_urls("product placeholder image", driver)
    if no_image_urls:
        no_image_path = os.path.join(images_dir, 'no-image.png')
        if download_image(no_image_urls[0], no_image_path, size=(400, 400)):
            print("No-image placeholder downloaded successfully")
    
    profile_urls = get_image_urls("default user profile picture", driver)
    if profile_urls:
        profile_path = os.path.join(images_dir, 'default-profile.png')
        if download_image(profile_urls[0], profile_path, size=(150, 150)):
            print("Default profile picture downloaded successfully")
    
    driver.quit()

if __name__ == '__main__':
    download_static_images() 