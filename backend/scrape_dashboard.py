import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to https://pindrop.host/dashboard")
        await page.goto("https://pindrop.host/dashboard")
        
        print("Waiting for email input...")
        # Usually, they have an input field of type email
        await page.wait_for_selector('input[type="email"]')
        await page.fill('input[type="email"]', 'drakesmart91@gmail.com')
        
        print("Waiting for password input...")
        await page.wait_for_selector('input[type="password"]')
        await page.fill('input[type="password"]', '@Babatunde112')
        
        print("Submitting login form...")
        # Press enter to submit
        await page.press('input[type="password"]', 'Enter')
        
        print("Waiting for dashboard to load...")
        # Wait for navigation to complete and URL to be /dashboard or similar
        await page.wait_for_url("**/dashboard**", timeout=15000)
        
        # Give it a couple seconds to fully render React components
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        
        # Fix paths
        content = content.replace('href="/_next/', 'href="./_next/')
        content = content.replace('src="/_next/', 'src="./_next/')
        content = content.replace('srcset="/_next/', 'srcset="./_next/')
        content = content.replace(', /_next/', ', ./_next/')
        content = content.replace('href="/favicon.ico', 'href="./favicon.ico')
        content = content.replace('href="/icon.png', 'href="./icon.png')
        content = content.replace('href="/apple-icon.png', 'href="./apple-icon.png')
        
        out_path = r'c:\Users\Admin\Documents\tech work\javis\new-project\jarvis\backend\templates\pindrop_kit\dashboard.html'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Dashboard HTML saved successfully!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
