import os
import requests
from datetime import datetime
from pydantic import BaseModel, Field
import re
from bs4 import BeautifulSoup


class Tools:
    def __init__(self):
        pass

    # Add your custom tools using pure Python code here, make sure to add type hints and descriptions

    def get_user_name_and_email_and_id(self, __user__: dict = {}) -> str:
        """
        Get the user name, Email and ID from the user object.
        """

        # Do not include a descrption for __user__ as it should not be shown in the tool's specification
        # The session user object will be passed as a parameter when the function is called

        print(__user__)
        result = ""

        if "name" in __user__:
            result += f"User: {__user__['name']}"
        if "id" in __user__:
            result += f" (ID: {__user__['id']})"
        if "email" in __user__:
            result += f" (Email: {__user__['email']})"

        if result == "":
            result = "User: Unknown"

        return result

    def get_current_time(self) -> str:
        """
        Get the current time in a more human-readable format.
        """

        now = datetime.now()
        current_time = now.strftime("%I:%M:%S %p")  # Using 12-hour format with AM/PM
        current_date = now.strftime(
            "%A, %B %d, %Y"
        )  # Full weekday, month name, day, and year

        return f"Current Date and Time = {current_date}, {current_time}"

    def calculator(
        self,
        equation: str = Field(
            ..., description="The mathematical equation to calculate."
        ),
    ) -> str:
        """
        Calculate the result of an equation.
        """

        # Avoid using eval in production code
        # https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
        try:
            result = eval(equation)
            return f"{equation} = {result}"
        except Exception as e:
            print(e)
            return "Invalid equation"

    def get_current_weather(
        self,
        city: str = Field(
            "New York, NY", description="Get the current weather for a given city."
        ),
    ) -> str:
        """
        Get the current weather for a given city.
        """

        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return (
                "API key is not set in the environment variable 'OPENWEATHER_API_KEY'."
            )

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",  # Optional: Use 'imperial' for Fahrenheit
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            data = response.json()

            if data.get("cod") != 200:
                return f"Error fetching weather data: {data.get('message')}"

            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            return f"Weather in {city}: {temperature}°C"
        except requests.RequestException as e:
            return f"Error fetching weather data: {str(e)}"

    def get_skku_news(self, limit: int = 5) -> str:
        """
        Fetch the latest news from Sungkyunkwan University (SKKU) website.
        
        Args:
            limit: The number of news items to return (default: 5)
            
        Returns:
            A formatted string with news titles, dates, and URLs.
        """
        """
        Fetch the latest news from Sungkyunkwan University (SKKU) website.
        Returns a formatted string with news titles, dates, and URLs.
        """
        try:
            # URL of the SKKU main page
            url = "https://www.skku.edu/skku/index.do"
            
            # Set up headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            # Create a session to handle cookies
            session = requests.Session()
            
            # Send a GET request to the website
            response = session.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the news section
            news_items = []
            
            # Print page content for debugging
            print(f"Page content length: {len(response.text)}")
            print(f"Response status code: {response.status_code}")
            
            # Let's try to get the "News and Announcements" section specifically
            # Try to fetch the main news page for better results
            main_news_url = "https://www.skku.edu/skku/campus/skk_comm/news.do"
            print(f"Trying to fetch news from: {main_news_url}")
            
            # Send another request to the main news page
            news_response = session.get(main_news_url, headers=headers)
            if news_response.status_code == 200:
                print(f"Successfully fetched main news page")
                # Update soup to use the news page
                soup = BeautifulSoup(news_response.text, 'html.parser')
            
            # Try multiple selectors to find news items
            selectors = [
                ".board-list li a",            # Board list items
                ".news-list a",                # Original selector
                ".board-wrap a",               # Board wrapper links
                "a.board-item",                # Board item links
                "a[href*='articleNo']",        # Links with article numbers
                ".board-row a",                # Board row links
                "tbody tr td a",               # Table cells with links
                ".notice-list a"               # Notice list links
            ]
            
            found_items = False
            # Try each selector
            for selector in selectors:
                news_section = soup.select(selector)
                print(f"Selector '{selector}' found {len(news_section)} items")
                
                if len(news_section) > 0:
                    found_items = True
                    break
                    
            if not found_items:
                # If no specific selectors worked, try more generic ones
                news_section = soup.select("a[href*='mode=view']")
                print(f"Generic selector found {len(news_section)} items")
            
            # Process each news item
            for item in news_section:
                # Get the URL - SKKU uses relative URLs
                news_url = item.get('href')
                if news_url:
                    if not news_url.startswith('http'):
                        # Handle URLs that start with just parameters
                        if news_url.startswith('?'):
                            news_url = f"https://www.skku.edu/skku/campus/skk_comm/news.do{news_url}"
                        else:
                            news_url = f"https://www.skku.edu{news_url}"
                
                # Get the title and date
                title = item.get_text(strip=True)
                
                # Look for date in different formats
                date_span = item.select_one(".date") or item.select_one(".board-date") or item.select_one(".datetime")
                date = date_span.get_text(strip=True) if date_span else ""
                
                # If no date found in the element itself, try parent or siblings
                if not date:
                    # Try to find date in parent or sibling elements
                    parent = item.parent
                    if parent:
                        date_elem = parent.select_one(".date") or parent.select_one(".board-date")
                        if date_elem:
                            date = date_elem.get_text(strip=True)
                
                # Clean up the title
                # Remove date from title if it's part of the text
                if date and date in title:
                    title = title.replace(date, "").strip()
                
                # Clean up the title further by removing any special characters at the start/end
                title = title.strip(' \t\n\r·:,;')
                
                # Add to our list if we have a title and URL
                if title and news_url:
                    # Some specifics for this website - filter out navigation links
                    skip_keywords = ['자세히 보기', '더보기', '목록', '검색', 'login', 'previous', 'next']
                    if not any(keyword in title.lower() for keyword in skip_keywords):
                        news_items.append({
                            "title": title,
                            "url": news_url,
                            "date": date
                        })
                
                # Stop when we reach the limit
                if len(news_items) >= limit:
                    break
            
            # If no news found, try an alternative approach
            if not news_items:
                # Look for news in a different format that might be present
                alt_news = soup.select(".news-inner")
                for news in alt_news[:limit]:
                    link = news.select_one("a")
                    if link:
                        title = link.get_text(strip=True)
                        news_url = link.get('href')
                        if news_url and not news_url.startswith('http'):
                            news_url = f"https://www.skku.edu{news_url}"
                        
                        date_elem = news.select_one(".date")
                        date = date_elem.get_text(strip=True) if date_elem else ""
                        
                        if title:
                            news_items.append({
                                "title": title,
                                "url": news_url,
                                "date": date
                            })
            
            # Format the results
            if news_items:
                result = "📰 Latest News from Sungkyunkwan University (SKKU):\n\n"
                for idx, item in enumerate(news_items, 1):
                    result += f"{idx}. {item['title']}"
                    if item['date']:
                        result += f" ({item['date']})"
                    result += f"\n   🔗 {item['url']}\n\n"
                return result
            else:
                return "Could not find any news on the SKKU website. Please check back later or visit https://www.skku.edu/skku/index.do directly."
                
        except requests.RequestException as e:
            return f"Error fetching news from SKKU: {str(e)}\nPlease visit the official website at https://www.skku.edu/skku/index.do"
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error parsing SKKU website: {error_details}")
            return f"Error processing news from SKKU: {str(e)}\nPlease visit the official website at https://www.skku.edu/skku/index.do"
