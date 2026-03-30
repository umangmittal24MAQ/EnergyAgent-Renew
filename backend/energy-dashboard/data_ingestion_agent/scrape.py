from playwright.sync_api import sync_playwright
import json
import os
import sys
from datetime import datetime

# Fix Unicode encoding on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

captured_data = []

def capture_api(response):
    try:
        # Capture XHR / fetch requests
        if response.request.resource_type in ["xhr", "fetch"]:
            print("\n📡 API URL:", response.url)

            try:
                data = response.json()

                print("📊 DATA:")
                print(json.dumps(data, indent=2))

                # ✅ Store clean structured data
                captured_data.append({
                    "url": response.url,
                    "data": data
                })

            except:
                print("⚠️ Not JSON response")

    except Exception as e:
        print("Error:", e)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Attach listener BEFORE navigation
        page.on("response", capture_api)

        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\n🗓️  Today's Date: {today}")
        print("=" * 60)
        print("Opening site...")
        page.goto("https://cloud.suryalog.com")

        print("Attempting automatic login...")
        # Wait for login form to appear
        page.wait_for_selector('#loginId', timeout=10000)
        
        # Fill in credentials
        page.fill('#loginId', "MAQ_Software")
        page.wait_for_timeout(500)
        page.fill('#password', "MAQ@1234")
        page.wait_for_timeout(500)
        
        # Click login button using the correct ID
        page.click('#btnlogin')
        print("Login button clicked, waiting for page to load...")
        
        # Wait for page to navigate after login
        page.wait_for_timeout(8000)

        # ========== ROBUST DATE NAVIGATION STRATEGY ==========
        print("\n📅 Navigating to today's data...")
        print(f"   Target date: {today}")
        
        # Strategy 1: Try JavaScript date manipulation
        print("  [1/5] Attempting JavaScript date manipulation...")
        try:
            # Try to set date via JavaScript
            page.evaluate(f"""
                () => {{
                    // Try to find and update all date inputs
                    const inputs = document.querySelectorAll('input[type="date"]');
                    inputs.forEach(input => {{
                        input.value = '{today}';
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }});
                    
                    // Try to find and click today buttons
                    const buttons = Array.from(document.querySelectorAll('button')).filter(b => 
                        b.textContent.toLowerCase().includes('today')
                    );
                    buttons.forEach(btn => btn.click());
                }}
            """)
            page.wait_for_timeout(3000)
            print("     ✓ JavaScript date operations attempted")
        except Exception as e:
            print(f"     ✗ JavaScript approach failed: {str(e)[:60]}")
        
        # Strategy 2: Try filling date inputs with multiple formats
        print("  [2/5] Trying date input fields...")
        try:
            date_inputs = page.query_selector_all('input[type="date"]')
            if date_inputs:
                for inp in date_inputs:
                    try:
                        page.fill('input[type="date"]', today)
                        page.wait_for_timeout(500)
                        page.press('input[type="date"]', 'Enter')
                        page.wait_for_timeout(2000)
                        print("     ✓ Set date via input field")
                        break
                    except:
                        continue
        except Exception as e:
            print(f"     ✗ Date input approach failed: {str(e)[:60]}")
        
        # Strategy 3: Try keyboard navigation (arrow keys to navigate to today)
        print("  [3/5] Attempting keyboard navigation...")
        try:
            # Focus on page and use arrow keys multiple times
            page.press('body', 'Tab')
            page.wait_for_timeout(500)
            for _ in range(5):
                page.press('body', 'ArrowRight')
                page.wait_for_timeout(300)
            print("     ✓ Keyboard navigation attempted")
        except Exception as e:
            print(f"     ✗ Keyboard navigation failed: {str(e)[:60]}")
        
        # Strategy 4: Look for "today" related buttons/links
        print("  [4/5] Looking for 'today' navigation elements...")
        try:
            # Try clicking buttons that might have "today" text
            today_buttons = page.query_selector_all('button, a, span')
            for elem in today_buttons:
                try:
                    text = page.evaluate('(el) => el.textContent || el.innerText || el.value', elem)
                    if text and 'today' in str(text).lower():
                        page.click(elem)
                        page.wait_for_timeout(2000)
                        print(f"     ✓ Clicked 'today' element")
                        break
                except:
                    continue
        except Exception as e:
            print(f"     ✗ 'Today' button search failed: {str(e)[:60]}")
        
        # Strategy 5: Click multiple areas of the page to trigger data refresh for today
        print("  [5/5] Triggering interactions to load today's data...")
        try:
            click_positions = [
                (page.viewport_size["width"] // 2, 100),      # Top center
                (page.viewport_size["width"] // 2, page.viewport_size["height"] // 2),  # Center
                (page.viewport_size["width"] - 100, 100),    # Top right
                (page.viewport_size["width"] // 4, page.viewport_size["height"] // 4),  # Upper left quadrant
            ]
            
            for x, y in click_positions:
                try:
                    page.mouse.click(x, y)
                    page.wait_for_timeout(1500)
                except:
                    continue
            print("     ✓ Page interactions triggered")
        except Exception as e:
            print(f"     ✗ Interaction triggering failed: {str(e)[:60]}")
        
        print("\n✓ Date navigation strategies completed")
        print("Waiting for all APIs to be triggered...")
        page.wait_for_timeout(8000)

        print("🔄 Reloading page to capture complete today's data...")
        page.reload()
        page.wait_for_timeout(10000)

        print("✓ Scraping complete, closing browser...")
        browser.close()
        
except Exception as e:
    print(f"\n⚠️ Browser automation error: {str(e)}")
    print("Continuing to save captured data if any...")

# ✅ Save all captured data into separate file
output_file = os.path.join(script_dir, "captured_api_data.json")

try:
    with open(output_file, "w") as f:
        json.dump(captured_data, f, indent=2)
    
    if captured_data:
        print(f"\n✅ Data saved successfully to {output_file}")
        print(f"   Total API calls captured: {len(captured_data)}")
        print(f"   Expected data date: {today}")
    else:
        print(f"\n⚠️ No API data captured, but file created at {output_file}")
        print("   This may happen if login failed or APIs were not triggered")
        
except Exception as e:
    print(f"\n❌ Error saving data to {output_file}: {str(e)}")
    sys.exit(1)