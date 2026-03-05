import json
import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

# Helper to get paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def scrape_scheme(context, scheme):
    print(f"Scraping {scheme['scheme_name']}...")
    page = await context.new_page()
    try:
        await page.goto(scheme['url'], wait_until="networkidle")
        
        async def extract_value(label):
            try:
                loc = page.get_by_text(label, exact=False).first
                parent = loc.locator("..")
                return await parent.locator("span,div").last.inner_text()
            except:
                return "N/A"

        scheme['expense_ratio'] = await extract_value("Expense Ratio")
        scheme['exit_load'] = await extract_value("Exit Load")
        scheme['aum'] = await extract_value("AUM")
        scheme['nav'] = await extract_value("NAV")
        scheme['min_sip'] = await extract_value("Minimum SIP")
        scheme['min_lumpsum'] = await extract_value("Minimum Lumpsum")
        scheme['lock_in'] = await extract_value("Lock-in")
        scheme['turnover'] = await extract_value("Turnover Ratio")
        
        # New Metrics
        scheme['fund_manager'] = await extract_value("Fund Manager")
        scheme['return_1y'] = await extract_value("1Y Return")
        scheme['return_3y'] = await extract_value("3Y Return")
        scheme['return_5y'] = await extract_value("5Y Return")
        
        try:
            risk = await page.locator(".riskometer-text").first.inner_text()
            scheme['risk'] = risk.strip()
        except:
            scheme['risk'] = "Very High"

        scheme['benchmark'] = await extract_value("Benchmark")
        
    except Exception as e:
        print(f"Error scraping {scheme['scheme_name']}: {e}")
    finally:
        await page.close()

async def main():
    data_path = os.path.join(PROJECT_ROOT, 'data/funds.json')
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    with open(data_path, 'r') as f:
        schemes = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        tasks = [scrape_scheme(context, scheme) for scheme in schemes]
        await asyncio.gather(*tasks)
        
        await browser.close()

    # Add last_updated timestamp to each scheme
    last_updated = datetime.now().isoformat()
    for scheme in schemes:
        scheme['last_updated'] = last_updated
    
    with open(data_path, 'w') as f:
        json.dump(schemes, f, indent=2)
    print(f"Data update complete. {len(schemes)} schemes saved to {data_path}.")
    print(f"Last updated timestamp: {last_updated}")

if __name__ == "__main__":
    asyncio.run(main())
