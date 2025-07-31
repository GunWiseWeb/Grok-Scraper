from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
from bs4 import BeautifulSoup

# Set up headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

# List to hold scraped data
data = []

# Loop through all 278 pages
for page in range(1, 279):
    url = f"https://www.rkguns.com/firearms.html?page={page}&numResults=36"
    driver.get(url)
    
    # Wait for product grid to load (timeout after 20 seconds)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item-link")))
    except:
        print(f"Timeout loading page {page}. Skipping.")
        continue
    
    # Parse the page source
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find all product links (standard class for this site structure)
    product_links = soup.select('a.product-item-link')
    
    for link in product_links:
        product_url = link['href']
        driver.get(product_url)
        
        # Wait for specs table to load
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.data.table.additional-attributes")))
        except:
            print(f"Timeout loading product: {product_url}. Skipping.")
            continue
        
        # Parse product page
        product_soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Get product name for type inference
        name_tag = product_soup.find('h1', class_='page-title')
        name = name_tag.text.strip() if name_tag else ''
        
        # Infer firearm type from name
        firearm_type = 'Unknown'
        lower_name = name.lower()
        if 'pistol' in lower_name or 'handgun' in lower_name:
            firearm_type = 'Pistol'
        elif 'revolver' in lower_name:
            firearm_type = 'Revolver'
        elif 'rifle' in lower_name:
            firearm_type = 'Rifle'
        elif 'shotgun' in lower_name:
            firearm_type = 'Shotgun'
        
        # Extract specs from table
        specs_table = product_soup.find('table', class_='data table additional-attributes')
        upc = ''
        mpn = ''
        caliber = ''
        if specs_table:
            rows = specs_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue
                label = row.find('th').text.strip() if row.find('th') else ''
                value = cells[0].text.strip()  # In the table structure, it's th for label, td for value
                if label == 'UPC':
                    upc = value
                elif label == 'MPN':
                    mpn = value
                elif label == 'Caliber':
                    caliber = value
        
        # Append if any data was found
        if upc or mpn or caliber or firearm_type != 'Unknown':
            data.append([upc, mpn, caliber, firearm_type])
    
    # Polite delay to avoid overwhelming the server
    time.sleep(2)

# Write to CSV
with open('firearms_inventory.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['UPC', 'MPN', 'Caliber', 'Type'])
    writer.writerows(data)

driver.quit()
print("Scraping complete. Data saved to firearms_inventory.csv")
