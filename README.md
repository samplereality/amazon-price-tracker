# Amazon Price Tracker

A Python script that monitors Amazon product prices and sends email notifications when prices drop below your target threshold. Designed to run on a Raspberry Pi 4 via cron jobs for automated daily monitoring.

## Features

- Scrapes Amazon product prices using BeautifulSoup
- Sends HTML email alerts when price drops below target
- Configurable via environment variables or JSON configuration file
- Secure credential management with .env files
- Handles multiple price selectors for reliability
- Respectful scraping with delays
- Easy deployment on Raspberry Pi

## Requirements

- Python 3.7 or higher
- Internet connection
- Email account for sending notifications (Gmail recommended)

## Installation

### On Your Development Machine

1. Clone or download this repository:
```bash
cd /path/to/amazon-price-tracker
```

2. Create a virtual environment:
```bash
python3 -m venv venv
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### On Raspberry Pi 4

1. Transfer files to your Raspberry Pi:
```bash
scp -r /path/to/amazon-price-tracker pi@raspberrypi.local:~/
```

2. SSH into your Raspberry Pi:
```bash
ssh pi@raspberrypi.local
```

3. Navigate to the project directory:
```bash
cd ~/amazon-price-tracker
```

4. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The script supports two configuration methods: **environment variables (recommended for production)** or a JSON configuration file. Environment variables take precedence over the config file.

### Method 1: Environment Variables (Recommended)

This method is ideal for production deployments and keeping sensitive data out of version control.

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```bash
# Amazon Product Settings
PRODUCT_NAME=Example Product Name
PRODUCT_URL=https://www.amazon.com/dp/PRODUCT_ID
TARGET_PRICE=50.00

# Email Settings (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@gmail.com
EMAIL_PASSWORD=your-app-specific-password

# Optional Settings
NOTIFY_ON_ERROR=false
```

**Security Note:** The `.env` file is automatically excluded from git via `.gitignore`. Never commit this file with real credentials.

### Method 2: JSON Configuration File (Alternative)

If you prefer JSON configuration:

1. Copy the example configuration file:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your settings:
```json
{
  "product": {
    "name": "Your Product Name",
    "url": "https://www.amazon.com/dp/YOUR_PRODUCT_ID",
    "target_price": 50.00
  },
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "your-email@gmail.com",
    "to_email": "recipient@gmail.com",
    "password": "your-app-specific-password"
  },
  "notify_on_error": false
}
```

**Note:** Environment variables will override values in `config.json` if both are present.

### Finding the Amazon Product URL

- Navigate to the product page on Amazon
- Copy the URL from your browser
- You can use the full URL or just the shortened version: `https://www.amazon.com/dp/PRODUCT_ID`

### Setting Up Gmail for Email Notifications

If using Gmail, you need to create an **App Password**:

1. Go to your Google Account settings
2. Enable 2-Factor Authentication if not already enabled
3. Go to Security > 2-Step Verification > App passwords
4. Generate a new app password for "Mail"
5. Use this 16-character password in your `.env` or `config.json`

### Configuration on Raspberry Pi

For Raspberry Pi deployments, you can either:

1. **Use a .env file** (recommended): Transfer your `.env` file to the Pi
2. **Set system environment variables**: Add exports to your `.bashrc` or `.profile`
3. **Set in crontab**: Add environment variables directly in your crontab file

Example crontab with environment variables:
```
# Set environment variables
PRODUCT_URL=https://www.amazon.com/dp/YOUR_PRODUCT_ID
TARGET_PRICE=50.00
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@gmail.com
EMAIL_PASSWORD=your-app-password

# Run price tracker daily at 9 AM
0 9 * * * /home/pi/amazon-price-tracker/venv/bin/python /home/pi/amazon-price-tracker/price_tracker.py >> /home/pi/amazon-price-tracker/cron.log 2>&1
```

## Usage

### Manual Test Run

Activate the virtual environment and run the script:

```bash
source venv/bin/activate
python price_tracker.py
```

You should see output like:
```
============================================================
Checking price for: Your Product Name
Time: 2025-11-01 10:30:00
============================================================
Current Price: $45.99
Target Price: $50.00
🎉 PRICE DROP ALERT! Current price ($45.99) is at or below target ($50.00)
Email sent successfully to recipient@gmail.com
============================================================
```

### Setting Up Daily Cron Job on Raspberry Pi

1. Make the script executable:
```bash
chmod +x price_tracker.py
```

2. Open crontab editor:
```bash
crontab -e
```

3. Add one of the following lines to run the script daily:

Run every day at 9:00 AM:
```
0 9 * * * /home/pi/amazon-price-tracker/venv/bin/python /home/pi/amazon-price-tracker/price_tracker.py >> /home/pi/amazon-price-tracker/cron.log 2>&1
```

Run every day at 9:00 AM and 6:00 PM:
```
0 9,18 * * * /home/pi/amazon-price-tracker/venv/bin/python /home/pi/amazon-price-tracker/price_tracker.py >> /home/pi/amazon-price-tracker/cron.log 2>&1
```

4. Save and exit the editor

### Cron Schedule Examples

- `0 9 * * *` - Daily at 9:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 9,18 * * *` - Twice daily (9 AM and 6 PM)
- `0 12 * * 1` - Every Monday at noon

### Viewing Cron Logs

Check the log file to see script output:
```bash
tail -f ~/amazon-price-tracker/cron.log
```

### Verify Cron Job Status

List your cron jobs:
```bash
crontab -l
```

## Troubleshooting

### Price Not Found

If the script can't find the price, Amazon may have changed their HTML structure. The script tries multiple selectors, but you may need to:

1. Visit the product page in a browser
2. Right-click the price and select "Inspect"
3. Find the HTML element containing the price
4. Update the `price_selectors` list in [price_tracker.py](price_tracker.py)

### Email Not Sending

- Verify SMTP settings in your `.env` file or `config.json`
- For Gmail, ensure you're using an App Password, not your regular password
- Check if 2-Factor Authentication is enabled
- Verify your internet connection
- Check firewall settings on Raspberry Pi

### Script Not Running via Cron

- Verify the paths in your crontab are absolute paths
- Check the cron log file for errors
- Ensure the virtual environment path is correct
- Verify the script has execute permissions: `chmod +x price_tracker.py`
- Test the exact cron command manually first

### Amazon Blocking Requests

If you're getting blocked:

- The script includes a 2-second delay between requests
- Don't run the script too frequently (once or twice daily is recommended)
- Amazon may temporarily block if they detect scraping
- Consider using a VPN or rotating user agents

## Important Notes

### Legal and Ethical Considerations

- This script is for personal use only
- Amazon's Terms of Service may prohibit automated scraping
- Use responsibly and don't overload Amazon's servers
- Running once or twice daily is recommended
- Consider using the Amazon Product Advertising API for commercial use

### Privacy and Security

- Never commit `.env` or `config.json` files with real credentials to git
- Both files are automatically excluded via `.gitignore`
- Use app-specific passwords, not your main email password
- Keep your Raspberry Pi software updated
- Environment variables are the recommended method for managing sensitive data

## Project Structure

```
amazon-price-tracker/
├── price_tracker.py        # Main script
├── .env.example           # Environment variables template
├── .env                   # Your actual environment variables (gitignored)
├── config.example.json     # JSON configuration template (alternative)
├── config.json            # Your actual JSON config (gitignored, optional)
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── venv/                 # Virtual environment (gitignored)
```

## Future Enhancements

Possible improvements you could add:

- Track price history in a SQLite database
- Support multiple products in one config
- Generate price trend graphs
- Support other e-commerce sites
- Web dashboard for viewing tracked products
- Telegram/SMS notifications
- Price prediction using historical data

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
