import os
import time
from dotenv import load_dotenv
import requests
import base64

# Load environment variables
load_dotenv()

# Get variables from environment
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
OWNER = os.getenv("Owner")
REPO = os.getenv("Repository")

# GitHub API base URL
BASE_URL = "https://api.github.com"
HEADERS = {"Authorization": f"token {GITHUB_API_KEY}"}

def create_branch(owner, repo, base_branch, new_branch_prefix):
    base_branch_url = f"{BASE_URL}/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
    response = requests.get(base_branch_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to get base branch info. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

    base_sha = response.json()['object']['sha']

    # Generate a unique branch name
    timestamp = int(time.time())
    new_branch = f"{new_branch_prefix}-{timestamp}"

    create_branch_url = f"{BASE_URL}/repos/{owner}/{repo}/git/refs"
    data = {
        "ref": f"refs/heads/{new_branch}",
        "sha": base_sha
    }
    response = requests.post(create_branch_url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"Branch {new_branch} created successfully in {owner}/{repo}.")
        return new_branch
    else:
        print(f"Failed to create branch. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

def update_file_in_branch(owner, repo, file_path, branch, content):
    file_url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    response = requests.get(file_url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to get file info. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return False

    response_data = response.json()

    if isinstance(response_data, list):
        print(f"The path '{file_path}' refers to a directory. Skipping.")
        return False

    update_url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
    data = {
        "message": f"Update file {file_path}",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
        "sha": response_data["sha"]
    }
    
    response = requests.put(update_url, headers=HEADERS, json=data)
    if response.status_code in [200, 201]:
        print(f"File {file_path} updated successfully in branch {branch} of {owner}/{repo}.")
        return True
    else:
        print(f"Failed to update file {file_path}. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return False

def update_multiple_files(owner, repo, file_paths, new_content):
    new_branch = create_branch(owner, repo, "main", "feature-multi-update")
    if not new_branch:
        return

    success_count = 0
    for file_path in file_paths:
        if update_file_in_branch(owner, repo, file_path, new_branch, new_content):
            success_count += 1

    print(f"Updated {success_count} out of {len(file_paths)} files in branch {new_branch}.")

def main():
    if not all([GITHUB_API_KEY, OWNER, REPO]):
        print("Error: Missing required environment variables. Please check your .env file.")
        return

    # List of files to update
    files_to_update = [
        "_includes/slide.html",
        "_includes/head.html",
        "_includes/script.html"
    ]

    # Content to write to each file
    new_content = "This is the updated content for multiple files."

    update_multiple_files(OWNER, REPO, files_to_update, new_content)

if __name__ == "__main__":
    main()