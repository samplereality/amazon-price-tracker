# Troubleshooting Amazon Price Tracker

## Amazon Blocking / CAPTCHA Issues

Amazon actively blocks automated scrapers. If you're getting "Failed to retrieve price" errors, here are solutions:

### Immediate Solutions

1. **Enable Debug Mode** to see what Amazon is returning:
   ```bash
   # Add to your .env file
   DEBUG_MODE=true
   ```

   Run the script again, and it will save the HTML response to a file like `debug_response_20251101_120000.html`. Open this file to see if Amazon is showing a CAPTCHA page.

2. **Check the console output** - The script will now tell you:
   - The exact URL being fetched
   - HTTP response status code
   - If a CAPTCHA was detected

3. **Try accessing the URL manually first**:
   - Open the Amazon product URL in your browser
   - Solve any CAPTCHA if presented
   - This may temporarily whitelist your IP address
   - Then run the script

### Long-term Solutions

1. **Use a VPN or Proxy**:
   - Change your IP address using a VPN
   - Amazon may be rate-limiting or blocking your IP
   - Rotating between different IP addresses can help

2. **Reduce Frequency**:
   - Don't run the script too often
   - Once or twice daily is recommended
   - Amazon is more likely to block frequent requests

3. **Add Session Cookies** (Advanced):
   - Open Amazon in your browser
   - Copy your session cookies
   - Add them to the script's headers
   - This makes requests look more like they're coming from your browser

4. **Use Browser Automation** (Most Reliable):
   - Instead of requests + BeautifulSoup, use Selenium or Playwright
   - These tools actually run a real browser
   - Much harder for Amazon to detect
   - Requires more resources (not ideal for Raspberry Pi)

### Understanding the Error Messages

**"Response status code: 503"**
- Amazon's servers are temporarily unavailable or blocking you
- Wait 30-60 minutes and try again

**"WARNING: Amazon is blocking this request (CAPTCHA detected)"**
- Amazon has detected automated access
- Try the solutions above
- Access the URL in a browser first

**"Could not find price on page"**
- Either Amazon changed their HTML structure
- Or you're getting a blocked/CAPTCHA page
- Enable DEBUG_MODE to see the actual HTML

**"Error fetching URL: HTTPError"**
- Network issues or Amazon returned an error status code
- Check your internet connection
- The status code will be printed to help debug

## Alternative: Amazon Product Advertising API

For reliable, legal access to Amazon price data, consider using the official Amazon Product Advertising API:

- **Pros**: Legal, reliable, won't get blocked
- **Cons**: Requires application approval, complex setup
- **Link**: https://webservices.amazon.com/paapi5/documentation/

## Testing Your Setup

Run the script with debug mode enabled to diagnose issues:

```bash
# In your .env file:
DEBUG_MODE=true

# Then run:
python price_tracker.py
```

Look for:
- ✅ Status code 200 = Good
- ❌ Status code 503 = Blocked
- ❌ CAPTCHA detected = Blocked
- ❌ No price found = Wrong selectors or blocked

## Still Having Issues?

1. Verify your Amazon URL works in a browser
2. Check that your .env file is configured correctly
3. Ensure you're using a current Amazon product URL (not expired/deleted product)
4. Try a different Amazon product to rule out product-specific issues
5. Consider the frequency - are you running it too often?

## Example Debug Session

```bash
$ python price_tracker.py

============================================================
Checking price for: Example Product
Time: 2025-11-01 10:30:00
============================================================
Fetching URL: https://www.amazon.com/dp/B08N5WRWNW
Response status code: 503
WARNING: Amazon is blocking this request (CAPTCHA detected)
Try the following:
  1. Wait a few hours before trying again
  2. Use a VPN to change your IP address
  3. Try accessing the URL manually in a browser first
Failed to retrieve price. Will try again next run.
============================================================
```

This output clearly shows Amazon is blocking with a 503 status code and CAPTCHA.
