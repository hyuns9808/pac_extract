'''
Function that downloads KICS PaC query doc from official URL
KICS provides its combined query CSV via a JavaScript function within its doc website
Thus, using Selenium to run script similar to one written in website to download query
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import os
import time

def get_kics_queries(url):
    # Variables
    project_root = os.getcwd()
    save_dir = os.path.join(project_root, f"data/KICS")
    os.makedirs(save_dir,exist_ok=True)
    file_name = "all_queries.csv"
    # Step descriptions
    steps = [
        "Launching browser",
        "Loading page",
        "Waiting for updated elements",
        "Injecting JS hook",
        "Launching download query",
        "Waiting for CSV data",
        "Saving CSV file",
        "Done"
    ]
    # === Set up headless browser ===
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    
    # Create progress bar
    progress = tqdm(total=len(steps), bar_format="{l_bar}{bar} [step {n_fmt}/{total_fmt}]")

    try:
        progress.set_description(steps[0])
        progress.update(1)
        driver.get(url)

        # === Wait for the download button ===
        progress.set_description(steps[1])
        progress.update(1)
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'btn-success') and contains(text(), 'Download')]"))
        )

        # === Hook the download function to capture the CSV string ===
        progress.set_description(steps[2])
        progress.update(1)
        driver.execute_script("""
        window._downloadedCSV = null;
        const originalDownloadCSV = downloadCSV;
        downloadCSV = function(csv, filename) {
            window._downloadedCSV = csv;
            return originalDownloadCSV(csv, filename);
        };
        """)

        # === Click the button (runs exportToCSV -> downloadCSV) ===
        progress.set_description(steps[3])
        progress.update(1)
        download_button = driver.find_element(By.XPATH, "//a[contains(@class, 'btn-success') and contains(text(), 'Download')]")
        download_button.click()

        # === Wait until the CSV is available in JS memory ===
        progress.set_description(steps[4])
        progress.update(1)
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return window._downloadedCSV !== null")
        )

        # === Get the CSV content ===
        progress.set_description(steps[5])
        progress.update(1)
        csv_data = driver.execute_script("return window._downloadedCSV")

        # === Save to file ===
        progress.set_description(steps[6])
        progress.update(1)
        save_dir = os.path.join(save_dir, file_name)
        with open(save_dir, "w", encoding="utf-8") as f:
            f.write(csv_data)
        
        # Done
        progress.set_description(steps[7])
        progress.update(1)
    finally:
        driver.quit()
        progress.close()
        print(f"✅ PaC data download from URL complete of tool:  KICS\n")

'''
if __name__ == '__main__':
    get_kics_queries()
'''