import os
from dotenv import load_dotenv
import requests
import base64

# Load environment variables from .env file
load_dotenv()

def check_repo_and_get_file(owner, repo, file_path, token):
    # GitHub API base URL
    base_url = "https://api.github.com"

    # Check if the repository exists
    repo_url = f"{base_url}/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {token}"}
    
    response = requests.get(repo_url, headers=headers)
    
    if response.status_code == 200:
        print(f"Repository {owner}/{repo} exists.")
        
        # Get the file content
        file_url = f"{base_url}/repos/{owner}/{repo}/contents/{file_path}"
        file_response = requests.get(file_url, headers=headers)
        
        if file_response.status_code == 200:
            file_data = file_response.json()
            if isinstance(file_data, list):
                print(f"The path '{file_path}' refers to a directory. Contents:")
                for item in file_data:
                    print(f"- {item['name']} ({'directory' if item['type'] == 'dir' else 'file'})")
            elif isinstance(file_data, dict) and "content" in file_data:
                content = file_data["content"]
                decoded_content = base64.b64decode(content).decode("utf-8")
                print(f"File content:\n{decoded_content}")
                return decoded_content
            else:
                print(f"Unexpected response format. Response data: {file_data}")
        else:
            print(f"Failed to retrieve file. Status code: {file_response.status_code}")
            print(f"Response content: {file_response.text}")
        return None
    else:
        print(f"Repository not found or access denied. Status code: {response.status_code}")
        return None

# Get variables from environment
github_api_key = os.getenv("GITHUB_API_KEY")
owner = os.getenv("Owner")
repo = os.getenv("Repository")
file_path = os.getenv("Repo_File_Path")

# Check if all required environment variables are set

if not all([github_api_key, owner, repo, file_path]):
    print("Error: Missing required environment variables. Please check your .env file.")
    print(f"GITHUB_API_KEY: {'Set' if github_api_key else 'Not Set'}")
    print(f"Owner: {'Set' if owner else 'Not Set'}")
    print(f"Repository: {'Set' if repo else 'Not Set'}")
    print(f"Repo_File_Path: {'Set' if file_path else 'Not Set'}")
else:
    try:
        check_repo_and_get_file(owner, repo, file_path, github_api_key)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your .env file and ensure all variables are set correctly.")
        print(f"Owner: {owner}")
        print(f"Repository: {repo}")
        print(f"Repo_File_Path: {file_path}")