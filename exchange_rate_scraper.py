import time
import logging
from datetime import datetime
import pandas as pd
import os
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import os
import smtplib
from email.message import EmailMessage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('western_union_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WesternUnionScraper:
    def __init__(self):
        self.setup_chrome_options()
        # Use Tunisia time for the CSV filename
        tz = pytz.timezone('Africa/Tunis')
        date_str = datetime.now(tz).strftime('%Y-%m-%d')
        self.results_file = f'exchange_rates_for_{date_str}.csv'
        self.max_retries = 3
        self.delay_between_requests = 3
        self.page_load_timeout = 30
        self.currency_pairs = [
            {
                'pair': 'EUR-TND',
                'url': 'https://www.westernunion.com/fr/fr/currency-converter/eur-to-tnd-rate.html',
                'provider': 'WesternUnion'
            },
            {
                'pair': 'EUR-MAD',
                'url': 'https://www.westernunion.com/fr/fr/currency-converter/eur-to-mad-rate.html',
                'provider': 'WesternUnion'
            },
            {
                'pair': 'EUR-TND',
                'url': 'https://www.moneygram.com/fr/en/corridor/tunisia',
                'provider': 'MoneyGram'
            },
            {
                'pair': 'EUR-MAD',
                'url': 'https://www.moneygram.com/fr/en/corridor/morocco',
                'provider': 'MoneyGram'
            },
            {
                'pair': 'EUR-TND',
                'url': 'https://lemfi.com/fr-pl/international-money-transfer/tunisia',
                'provider': 'LemFi',
                'currency': 'TND'
            },
            {
                'pair': 'EUR-MAD',
                'url': 'https://lemfi.com/fr-pl/international-money-transfer/morocco?amount=100&amountType=sending',
                'provider': 'LemFi',
                'currency': 'MAD'
            },
            {
                'pair': 'EUR-TND',
                'url': 'https://www.remitly.com/fr/fr/tunisia/pricing',
                'provider': 'Remitly',
                'currency': 'TND'
            },
            {
                'pair': 'EUR-MAD',
                'url': 'https://www.remitly.com/fr/fr/morocco/pricing',
                'provider': 'Remitly',
                'currency': 'MAD'
            },
            {
                'pair': 'EUR-TND',
                'url': 'https://www.riamoneytransfer.com/fr-fr/rates-conversion/?From=EUR&To=TND&Amount=1',
                'provider': 'Ria',
                'currency': 'TND'
            },
            {
                'pair': 'EUR-MAD',
                'url': 'https://www.riamoneytransfer.com/fr-ca/rates-conversion/?From=EUR&To=MAD&Amount=1',
                'provider': 'Ria',
                'currency': 'MAD'
            },
            {
                'pair': 'EUR-TND',
                'url': 'https://www.myeasytransfer.com/convertisseur-euro-dinar-tunisie',
                'provider': 'MyEasyTransfer',
                'currency': 'TND'
            },
            {
                'pair': 'EUR-MAD',
                'url': 'https://www.myeasytransfer.com/convertisseur-euro-mad-maroc',
                'provider': 'MyEasyTransfer',
                'currency': 'MAD'
            }
        ]

    def setup_chrome_options(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('--disable-plugins')

    def get_chromedriver_path(self):
        driver_path = ChromeDriverManager().install()
        if os.path.isfile(driver_path):
            return driver_path
        # For Windows, check for .exe
        exe_path = os.path.join(os.path.dirname(driver_path), 'chromedriver.exe')
        if os.path.isfile(exe_path):
            return exe_path
        # For Linux/Mac, check for 'chromedriver' without extension
        unix_path = os.path.join(os.path.dirname(driver_path), 'chromedriver')
        if os.path.isfile(unix_path):
            return unix_path
        raise Exception('Could not find a valid chromedriver')

    def get_rate(self, url: str, amount: float = 100) -> float:
        driver = None
        for attempt in range(self.max_retries):
            try:
                driver_path = self.get_chromedriver_path()
                driver = webdriver.Chrome(service=Service(driver_path), options=self.chrome_options)
                driver.set_page_load_timeout(self.page_load_timeout)
                driver.get(url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#wu-input-EUR")))
                # Set amount
                amount_input = driver.find_element(By.CSS_SELECTOR, "input#wu-input-EUR")
                amount_input.clear()
                amount_input.send_keys(str(amount))
                time.sleep(2)
                # Get the rate
                rate_elem = driver.find_element(By.CSS_SELECTOR, "span.fx-to")
                rate_text = rate_elem.text.strip()  # e.g., "3.4392 TND"
                rate = float(rate_text.split()[0].replace(',', '.'))
                logger.info(f"Extracted rate from {url}: 1 EUR = {rate}")
                driver.quit()
                return rate
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error extracting rate from {url}: {e}")
                if driver:
                    driver.quit()
                time.sleep(self.delay_between_requests)
        if driver:
            driver.quit()
        raise Exception(f"Failed to extract rate from {url} after retries")

    def get_moneygram_rate(self, url: str) -> float:
        driver = None
        for attempt in range(self.max_retries):
            try:
                driver_path = self.get_chromedriver_path()
                driver = webdriver.Chrome(service=Service(driver_path), options=self.chrome_options)
                driver.set_page_load_timeout(self.page_load_timeout)
                driver.get(url)
                # Try to accept cookies if a consent button is present
                try:
                    consent_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]"))
                    )
                    consent_btn.click()
                    logger.info("Clicked on cookie consent button.")
                    time.sleep(1)
                except Exception:
                    logger.info("No cookie consent button found or already accepted.")
                # Wait longer for the rate to appear
                WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.text-mgSuccess-500"))
                )
                # Take a screenshot for debugging
                screenshot_path = f"moneygram_debug_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot to {screenshot_path}")
                # Log all found rate elements
                rate_elems = driver.find_elements(By.CSS_SELECTOR, "span.text-mgSuccess-500")
                found_any = False
                for elem in rate_elems:
                    text = elem.text.strip()
                    logger.info(f"MoneyGram found text: {text}")
                    if text.startswith("1 EUR ="):
                        rate = float(text.split("=")[1].split()[0].replace(',', '.'))
                        driver.quit()
                        return rate
                    found_any = True
                if not found_any:
                    logger.error("No span.text-mgSuccess-500 elements found on the page.")
                driver.quit()
                raise Exception("Taux non trouvé sur la page MoneyGram")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error extracting rate from MoneyGram {url}: {e}")
                if driver:
                    driver.quit()
                time.sleep(self.delay_between_requests)
        if driver:
            driver.quit()
        raise Exception(f"Failed to extract rate from MoneyGram {url} after retries")

    def get_lemfi_rate(self, url: str, currency: str) -> float:
        driver = None
        for attempt in range(self.max_retries):
            try:
                driver_path = self.get_chromedriver_path()
                driver = webdriver.Chrome(service=Service(driver_path), options=self.chrome_options)
                driver.set_page_load_timeout(self.page_load_timeout)
                driver.get(url)
                driver.set_window_size(1920, 1080)
                time.sleep(2)
                # Attendre que le taux s'affiche
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.base-text--size-small--bold"))
                )
                elems = driver.find_elements(By.CSS_SELECTOR, "span.base-text--size-small--bold")
                for elem in elems:
                    text = elem.text.strip().replace('\xa0', ' ').replace('\u202f', ' ')
                    logger.info(f"LemFi found text: {text}")
                    if "1 EUR" in text and currency in text:
                        import re
                        match = re.search(r'1 EUR\s*=\s*([\d,.]+)\s*' + currency, text)
                        if match:
                            rate = float(match.group(1).replace(',', '.'))
                            driver.quit()
                            return rate
                driver.quit()
                raise Exception(f"Taux non trouvé sur la page LemFi pour {currency}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error extracting rate from LemFi {url}: {e}")
                if driver:
                    driver.quit()
                time.sleep(self.delay_between_requests)
        if driver:
            driver.quit()
        raise Exception(f"Failed to extract rate from LemFi {url} after {self.max_retries} retries")

    def get_remitly_rate(self, url: str, currency: str) -> float:
        driver = None
        for attempt in range(self.max_retries):
            try:
                driver_path = self.get_chromedriver_path()
                driver = webdriver.Chrome(service=Service(driver_path), options=self.chrome_options)
                driver.set_page_load_timeout(self.page_load_timeout)
                driver.get(url)
                driver.set_window_size(1920, 1080)
                time.sleep(2)
                # Attendre que le taux s'affiche
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.f4cg11h.ftw2f3l"))
                )
                elems = driver.find_elements(By.CSS_SELECTOR, "div.f4cg11h.ftw2f3l")
                for elem in elems:
                    text = elem.text.strip().replace('\xa0', ' ').replace('\u202f', ' ')
                    logger.info(f"Remitly found text: {text}")
                    if "1 EUR" in text and currency in text:
                        import re
                        match = re.search(r'1 EUR\s*=\s*([\d,.]+)\s*' + currency, text)
                        if match:
                            rate = float(match.group(1).replace(',', '.'))
                            driver.quit()
                            return rate
                driver.quit()
                raise Exception(f"Taux non trouvé sur la page Remitly pour {currency}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error extracting rate from Remitly {url}: {e}")
                if driver:
                    driver.quit()
                time.sleep(self.delay_between_requests)
        if driver:
            driver.quit()
        raise Exception(f"Failed to extract rate from Remitly {url} after {self.max_retries} retries")

    def get_ria_rate(self, url: str, currency: str) -> float:
        driver = None
        for attempt in range(self.max_retries):
            try:
                driver_path = self.get_chromedriver_path()
                driver = webdriver.Chrome(service=Service(driver_path), options=self.chrome_options)
                driver.set_page_load_timeout(self.page_load_timeout)
                driver.get(url)
                driver.set_window_size(1920, 1080)
                time.sleep(2)
                # Attendre que le taux s'affiche
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h3"))
                )
                elems = driver.find_elements(By.CSS_SELECTOR, "h3")
                for elem in elems:
                    text = elem.text.strip().replace('\xa0', ' ').replace('\u202f', ' ')
                    logger.info(f"Ria found text: {text}")
                    if "EUR" in text and currency in text:
                        import re
                        match = re.search(r'1[.,]0* EUR = ([\d,.]+) ' + currency, text)
                        if match:
                            rate = float(match.group(1).replace(',', '.'))
                            driver.quit()
                            return rate
                driver.quit()
                raise Exception(f"Taux non trouvé sur la page Ria pour {currency}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error extracting rate from Ria {url}: {e}")
                if driver:
                    driver.quit()
                time.sleep(self.delay_between_requests)
        if driver:
            driver.quit()
        raise Exception(f"Failed to extract rate from Ria {url} after {self.max_retries} retries")

    def get_myeasytransfer_rate(self, url: str, currency: str) -> float:
        driver = None
        for attempt in range(self.max_retries):
            try:
                driver_path = self.get_chromedriver_path()
                driver = webdriver.Chrome(service=Service(driver_path), options=self.chrome_options)
                driver.set_page_load_timeout(self.page_load_timeout)
                driver.get(url)
                driver.set_window_size(1920, 1080)
                time.sleep(2)
                # Attendre que le taux s'affiche
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.font-semibold"))
                )
                elems = driver.find_elements(By.CSS_SELECTOR, "div.font-semibold")
                for elem in elems:
                    text = elem.text.strip().replace('\xa0', ' ').replace('\u202f', ' ')
                    logger.info(f"MyEasyTransfer found text: {text}")
                    if "Votre Taux de change:" in text and currency in text:
                        import re
                        match = re.search(r'Votre Taux de change:.*?([\d,.]+).*?' + currency, text)
                        if match:
                            rate = float(match.group(1).replace(',', '.'))
                            driver.quit()
                            return rate
                driver.quit()
                raise Exception(f"Taux non trouvé sur la page MyEasyTransfer pour {currency}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error extracting rate from MyEasyTransfer {url}: {e}")
                if driver:
                    driver.quit()
                time.sleep(self.delay_between_requests)
        if driver:
            driver.quit()
        raise Exception(f"Failed to extract rate from MyEasyTransfer {url} after {self.max_retries} retries")

    def send_email_with_attachment(self, to_email, subject, body, attachment_path):
        sender_email = os.environ.get("SENDER_EMAIL") 
        app_password = os.environ.get("EMAIL_APP_PASSWORD")    

        msg = EmailMessage()
        msg["From"] = sender_email
        # Support both string and list for to_email
        if isinstance(to_email, list):
            msg["To"] = ", ".join(to_email)
        else:
            msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender_email, app_password)
                smtp.send_message(msg)
            logger.info(f"Email sent to {to_email} with attachment {file_name}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def scrape_and_save(self):
        tz = pytz.timezone('Africa/Tunis')
        current_time = datetime.now(tz)
        results = []
        for pair in self.currency_pairs:
            try:
                provider = pair.get('provider')
                if provider == 'MoneyGram':
                    rate = self.get_moneygram_rate(pair['url'])
                elif provider == 'LemFi':
                    rate = self.get_lemfi_rate(pair['url'], pair['currency'])
                elif provider == 'Remitly':
                    rate = self.get_remitly_rate(pair['url'], pair['currency'])
                elif provider == 'Ria':
                    rate = self.get_ria_rate(pair['url'], pair['currency'])
                elif provider == 'MyEasyTransfer':
                    rate = self.get_myeasytransfer_rate(pair['url'], pair['currency'])
                else:
                    rate = self.get_rate(pair['url'])
                results.append({
                    'datetime': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'indice': current_time.strftime('%H:%M (Tunisia)'),
                    'currency_pair': pair['pair'],
                    'provider': provider,
                    'rate': rate
                })
            except Exception as e:
                logger.error(f"Error scraping {pair['pair']} ({provider}): {e}")
        if results:
            df = pd.DataFrame(results)
            df.to_csv(self.results_file, index=False)
            logger.info(f"Created {self.results_file} with rates")
            # Send email with the CSV file
            self.send_email_with_attachment(
                to_email=["nouha@myeasytransfer.com", "ikbelghrab13@gmail.com"],
                subject="Exchange Rates",
                body="Hello, Here are the updated exchange rates for today.",
                attachment_path=self.results_file
            )
        else:
            logger.warning("No rates were scraped.")

    def run_once(self):
        logger.info("Running Western Union scraper once...")
        self.scrape_and_save()

def main():
    try:
        scraper = WesternUnionScraper()
        scraper.run_once()
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()