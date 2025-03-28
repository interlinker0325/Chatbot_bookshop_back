import requests
import base64

# input = input("Enter your input: ")
# api_token = "WfHCJas8H1D6JjMVrydUt56P"

def fetch_linkedin_profile(linkedin_url, api_token):
    # url = f"https://api.contactout.com/v1/people/linkedin?profile=https://www.linkedin.com/in/{input}&include_phone=true"
    api_endpoint = "https://api.contactout.com/v1/people/linkedin"
    headers = {
        "authorization": "basic",
        "token": api_token
    }
    params = {
        "profile": linkedin_url,
        "include_phone": "true"
    }

    try:
        response = requests.get(api_endpoint, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching LinkedIn profile: {e}")
        return None
    
if __name__ == "__main__":
    # Replace with your actual API token and LinkedIn profile URL
    api_token = "WfHCJas8H1D6JjMVrydUt56P"
    linkedin_url = "https://www.linkedin.com/in/mikemontano/"

    print("Fetching LinkedIn profile data...")
    profile_data = fetch_linkedin_profile(linkedin_url, api_token)

    if profile_data:
        print("Profile data retrieved successfully:")
        import json
        print(json.dumps(profile_data, indent=4))  # Pretty-print the JSON response
    else:
        print("Failed to retrieve profile data.")