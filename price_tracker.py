#!/usr/bin/env python3
"""
Amazon Price Tracker
Monitors Amazon product prices and sends email alerts when price drops below threshold.
"""

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AmazonPriceTracker:
    def __init__(self, config_file='config.json'):
        """Initialize the price tracker with configuration."""
        self.config = self.load_config(config_file)
        # Updated headers to better mimic a real browser (2025)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def load_config(self, config_file):
        """
        Load configuration from JSON file and environment variables.
        Environment variables take precedence over config file values.
        """
        config = {}

        # Load from config file if it exists (optional now)
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)

        # Override with environment variables (these take precedence)
        # Product settings
        config['product'] = {
            'name': os.getenv('PRODUCT_NAME', config.get('product', {}).get('name', 'Amazon Product')),
            'url': os.getenv('PRODUCT_URL', config.get('product', {}).get('url', '')),
            'target_price': float(os.getenv('TARGET_PRICE', config.get('product', {}).get('target_price', 0)))
        }

        # Email settings
        config['email'] = {
            'smtp_server': os.getenv('SMTP_SERVER', config.get('email', {}).get('smtp_server', 'smtp.gmail.com')),
            'smtp_port': int(os.getenv('SMTP_PORT', config.get('email', {}).get('smtp_port', 587))),
            'from_email': os.getenv('FROM_EMAIL', config.get('email', {}).get('from_email', '')),
            'to_email': os.getenv('TO_EMAIL', config.get('email', {}).get('to_email', '')),
            'password': os.getenv('EMAIL_PASSWORD', config.get('email', {}).get('password', ''))
        }

        # Optional settings
        config['notify_on_error'] = os.getenv('NOTIFY_ON_ERROR', 'false').lower() == 'true' or config.get('notify_on_error', False)

        # Validate required fields
        if not config['product']['url']:
            raise ValueError("PRODUCT_URL is required (set via environment variable or config.json)")
        if not config['email']['from_email']:
            raise ValueError("FROM_EMAIL is required (set via environment variable or config.json)")
        if not config['email']['to_email']:
            raise ValueError("TO_EMAIL is required (set via environment variable or config.json)")
        if not config['email']['password']:
            raise ValueError("EMAIL_PASSWORD is required (set via environment variable or config.json)")

        return config

    def get_price(self, url):
        """
        Scrape the price from an Amazon product page.

        Args:
            url: Amazon product URL

        Returns:
            tuple: (price as float, currency symbol) or (None, None) if not found
        """
        try:
            # Add a small delay to be respectful to Amazon's servers
            time.sleep(2)

            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)

            # Check response status
            print(f"Response status code: {response.status_code}")
            response.raise_for_status()

            # Check if we got a CAPTCHA or bot detection page
            if "api-services-support@amazon.com" in response.text or "Enter the characters you see below" in response.text:
                print("WARNING: Amazon is blocking this request (CAPTCHA detected)")
                print("Try the following:")
                print("  1. Wait a few hours before trying again")
                print("  2. Use a VPN to change your IP address")
                print("  3. Try accessing the URL manually in a browser first")
                return None, None

            soup = BeautifulSoup(response.content, 'lxml')

            # Amazon has multiple possible price selectors, try them in order
            price_selectors = [
                # Modern Amazon price selectors (as of 2025)
                '#corePrice_feature_div span.a-price.aok-align-center span.a-offscreen',
                '#corePrice_feature_div span.a-offscreen',
                'span.a-price.aok-align-center span.a-offscreen',
                '.a-price span.a-offscreen',
                # Legacy selectors
                'span.a-price-whole',
                'span.a-offscreen',
                'span#priceblock_ourprice',
                'span#priceblock_dealprice',
                'span.a-price span.a-offscreen',
            ]

            price_text = None
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text().strip()
                    break

            if not price_text:
                print("Warning: Could not find price on page. Amazon may have changed their HTML structure.")

                # Save HTML for debugging (optional - set DEBUG_MODE environment variable)
                if os.getenv('DEBUG_MODE', 'false').lower() == 'true':
                    debug_file = f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"Debug: Saved HTML response to {debug_file}")
                    print(f"Debug: Page title: {soup.title.string if soup.title else 'No title'}")

                return None, None

            # Clean the price string and extract numeric value
            # Remove currency symbols and convert to float
            price_cleaned = price_text.replace(',', '').replace('$', '').replace('£', '').replace('€', '').strip()

            # Extract just the numeric part (before any decimal or whole number)
            try:
                price = float(price_cleaned)
            except ValueError:
                # Try to extract just numbers and decimal point
                import re
                numbers = re.findall(r'\d+\.?\d*', price_cleaned)
                if numbers:
                    price = float(numbers[0])
                else:
                    return None, None

            # Determine currency symbol
            currency = '$'  # default
            if '£' in price_text:
                currency = '£'
            elif '€' in price_text:
                currency = '€'

            return price, currency

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None, None
        except Exception as e:
            print(f"Error parsing price: {e}")
            return None, None

    def send_email(self, subject, body):
        """
        Send an email notification.

        Args:
            subject: Email subject
            body: Email body (can include HTML)
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['email']['from_email']
            msg['To'] = self.config['email']['to_email']
            msg['Subject'] = subject

            # Attach the body
            msg.attach(MIMEText(body, 'html'))

            # Connect to SMTP server and send
            with smtplib.SMTP(self.config['email']['smtp_server'],
                            self.config['email']['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email']['from_email'],
                           self.config['email']['password'])
                server.send_message(msg)

            print(f"Email sent successfully to {self.config['email']['to_email']}")

        except Exception as e:
            print(f"Error sending email: {e}")

    def check_price(self):
        """
        Main function to check price and send alert if needed.
        """
        product_url = self.config['product']['url']
        target_price = self.config['product']['target_price']
        product_name = self.config['product'].get('name', 'Amazon Product')

        print(f"\n{'='*60}")
        print(f"Checking price for: {product_name}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        current_price, currency = self.get_price(product_url)

        if current_price is None:
            print("Failed to retrieve price. Will try again next run.")
            # Optionally send an error notification
            if self.config.get('notify_on_error', False):
                self.send_email(
                    f"Price Check Failed - {product_name}",
                    f"<p>Failed to check price for <strong>{product_name}</strong></p>"
                    f"<p>URL: {product_url}</p>"
                    f"<p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
                )
            return

        print(f"Current Price: {currency}{current_price:.2f}")
        print(f"Target Price: {currency}{target_price:.2f}")

        if current_price <= target_price:
            print(f"🎉 PRICE DROP ALERT! Current price ({currency}{current_price:.2f}) is at or below target ({currency}{target_price:.2f})")

            # Send email notification
            subject = f"Price Alert: {product_name} - Now {currency}{current_price:.2f}!"
            body = f"""
            <html>
                <body>
                    <h2 style="color: #28a745;">Price Drop Alert! 🎉</h2>
                    <p><strong>{product_name}</strong> is now available at your target price!</p>
                    <table style="border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Current Price:</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd; color: #28a745; font-size: 18px;">
                                <strong>{currency}{current_price:.2f}</strong>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Target Price:</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd;">{currency}{target_price:.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Savings:</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd;">{currency}{target_price - current_price:.2f}</td>
                        </tr>
                    </table>
                    <p><a href="{product_url}" style="background-color: #ff9900; color: white; padding: 10px 20px;
                       text-decoration: none; border-radius: 3px; display: inline-block;">View on Amazon</a></p>
                    <p style="color: #666; font-size: 12px;">Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </body>
            </html>
            """

            self.send_email(subject, body)
        else:
            print(f"Price is still above target. Difference: {currency}{current_price - target_price:.2f}")

        print(f"{'='*60}\n")


def main():
    """Main entry point for the script."""
    try:
        tracker = AmazonPriceTracker()
        tracker.check_price()
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
