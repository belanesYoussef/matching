import requests
import json
from urllib.parse import quote
import webbrowser
from datetime import datetime

# Configuration
API_KEY = '915b9665536748328a8c091c9b125a2b0b3235b73a3'
SCRAPEDO_URL = 'https://api.scrape.do'
UPWORK_SEARCH_TEMPLATE = "https://www.upwork.com/nx/search/talent/?q={}&location={}"

class ProfessionalFinder:
    def __init__(self):
        self.search_count = 0
        self.search_history = []
        self.api_active = True if API_KEY != '915b9665536748328a8c091c9b125a2b0b3235b73a3' else False

    def search(self, job_title, location='Remote', skills=None):
        """Main search function with multiple fallback methods"""
        self.search_count += 1
        search_data = {
            'id': f"search-{self.search_count}",
            'timestamp': datetime.now().isoformat(),
            'job_title': job_title,
            'location': location,
            'skills': skills or [],
            'results': None
        }

        print(f"\n🔎 Starting search #{self.search_count}...")

        # Try API if active
        if self.api_active:
            api_response = self.try_api_search(job_title, location, skills)
            if api_response and api_response.get('status') == 'success':
                search_data['results'] = api_response
                self.search_history.append(search_data)
                return api_response

        # Fallback to Upwork URL
        upwork_url = self.build_upwork_url(job_title, location, skills)
        result = {
            'status': 'fallback',
            'message': 'Using Upwork URL instead',
            'upwork_url': upwork_url,
            'profiles': []
        }
        search_data['results'] = result
        self.search_history.append(search_data)
        return result

    def try_api_search(self, job_title, location, skills):
        """Attempt API search with improved error handling"""
        try:
            print("Attempting API connection...")

            # Build the target URL we want to scrape
            target_url = self.build_upwork_url(job_title, location, skills, for_api=True)

            params = {
                'token': API_KEY,
                'url': target_url,
                'render': 'true',
                'timeout': '30000'
            }

            response = requests.get(
                SCRAPEDO_URL,
                params=params,
                headers={'Accept': 'application/json'},
                timeout=30
            )

            print(f"API response status: {response.status_code}")

            # Handle HTML responses that should be JSON
            if 'html' in response.headers.get('Content-Type', '').lower():
                print("⚠️ Received HTML instead of JSON response")
                print("This typically means:")
                print("- The API endpoint has changed")
                print("- You're being blocked by CAPTCHA")
                print("- Your plan doesn't allow this request")
                return None

            if response.status_code == 200:
                try:
                    data = response.json()
                    print("API response received successfully")
                    return self.parse_api_results(data)
                except json.JSONDecodeError:
                    print("⚠️ Failed to decode JSON response")
                    print(f"First 200 chars: {response.text[:200]}...")
                    return None
            else:
                print(f"API request failed with status {response.status_code}")
                print(f"Error: {response.text[:200]}...")
                return None

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {str(e)}")
            return None

    def build_upwork_url(self, job_title, location, skills, for_api=False):
        """Build Upwork search URL with proper parameters"""
        keywords = [job_title] + (skills or [])
        query = quote(' '.join(keywords))
        location_query = quote(location)

        url = UPWORK_SEARCH_TEMPLATE.format(query, location_query)

        # Add additional filters if needed
        if not for_api:
            url += "&hourly_rate=10-200"  # Example rate filter
            url += "&profile_type=independent"  # Freelancers only
        return url

    def parse_api_results(self, data):
        """Parse API response into standardized format"""
        print("Parsing API results...")

        profiles = []
        if isinstance(data, dict) and data.get('results'):
            for item in data['results']:
                name_parts = item.get('name', '').split()
                profile = {
                    'first_name': name_parts[0] if name_parts else '',
                    'last_name': ' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
                    'contact': {
                        'email': item.get('email'),
                        'phone': item.get('phone'),
                        'upwork': item.get('profile_url')
                    },
                    'skills': item.get('skills', []),
                    'bio': item.get('summary') or item.get('headline', ''),
                    'job_title': item.get('title', ''),
                    'location': item.get('location', ''),
                    'hourly_rate': item.get('hourly_rate'),
                    'rating': item.get('rating')
                }
                profiles.append(profile)

        return {
            'status': 'success',
            'count': len(profiles),
            'profiles': profiles
        } if profiles else None

    def display_results(self, results):
        """Display results with options to save or explore"""
        if not results:
            print("\n❌ No results found through any method.")
            return

        # Show basic info
        if results.get('status') == 'success':
            print(f"\n✅ Found {results['count']} profiles:")
            for profile in results['profiles'][:3]:
                print(f"\n👤 {profile.get('first_name', '')} {profile.get('last_name', '')}")
                print(f"💼 {profile.get('job_title', '')}")
                print(f"💰 Hourly Rate: {profile.get('hourly_rate', 'N/A')}")
                print(f"⭐ Rating: {profile.get('rating', 'N/A')}")
                print(f"📍 {profile.get('location', '')}")
                print(f"🛠️ Skills: {', '.join(profile.get('skills', []))}")
        elif results.get('upwork_url'):
            print("\n🔗 Upwork Search URL:")
            print(results['upwork_url'])
            print("\nWould you like to open this in your browser?")
            if input("(y/n): ").lower() == 'y':
                webbrowser.open(results['upwork_url'])

        # Save to JSON file
        if results.get('profiles') or results.get('upwork_url'):
            filename = f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Results saved to {filename}")
            except Exception as e:
                print(f"\n⚠️ Could not save results: {str(e)}")


def main():
    print("""
    ====================================
     ENHANCED PROFESSIONAL FINDER (UPWORK)
    ------------------------------------
     Searches for freelancers with:
     - Name/Contact Info
     - Skills
     - Hourly Rate
     - Ratings
    ====================================
    """)

    if '915b9665536748328a8c091c9b125a2b0b3235b73a3' in API_KEY:
        print("\n⚠️ IMPORTANT: You need to replace '915b9665536748328a8c091c9b125a2b0b3235b73a3'")
        print("with your actual Scrape.do API key to use API features.")
        print("Continuing with Upwork URL generation only...\n")

    finder = ProfessionalFinder()

    while True:
        print("\nEnter search criteria (or 'quit' to exit):")
        job_title = input("Job title/skill: ").strip()
        if job_title.lower() == 'quit':
            break

        location = input("Location [Remote]: ").strip() or 'Remote'
        skills = input("Skills (comma separated): ").strip()
        skills_list = [s.strip() for s in skills.split(',') if s.strip()]

        results = finder.search(job_title, location, skills_list)
        finder.display_results(results)

        print("\nWould you like to run another search?")
        if input("(y/n): ").lower() != 'y':
            break


if __name__ == "__main__":
    main()