import os
from dotenv import load_dotenv
import requests
import base64
import time

# Load environment variables from .env file
load_dotenv()

# Get variables from environment
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
OWNER = os.getenv("Owner")
REPO = os.getenv("Repository")
FILE_PATH = os.getenv("Repo_File_Path")

# GitHub API base URL
BASE_URL = "https://api.github.com"
HEADERS = {"Authorization": f"token {GITHUB_API_KEY}"}

def check_repo_exists(owner, repo):
    repo_url = f"{BASE_URL}/repos/{owner}/{repo}"
    response = requests.get(repo_url, headers=HEADERS)
    return response.status_code == 200

def create_repo(owner, repo):
    create_url = f"{BASE_URL}/user/repos"
    data = {"name": repo, "private": False}
    response = requests.post(create_url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"Repository {owner}/{repo} created successfully.")
    else:
        print(f"Failed to create repository. Status code: {response.status_code}")
        print(f"Response content: {response.text}")

def check_file_exists(owner, repo, file_path):
    file_url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
    response = requests.get(file_url, headers=HEADERS)
    return response.status_code == 200

def create_file(owner, repo, file_path, content):
    create_file_url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
    data = {
        "message": "Add new file",
        "content": base64.b64encode(content.encode()).decode()
    }
    response = requests.put(create_file_url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"File {file_path} created successfully in {owner}/{repo}.")
    else:
        print(f"Failed to create file. Status code: {response.status_code}")
        print(f"Response content: {response.text}")

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
        return

    response_data = response.json()

    if isinstance(response_data, list):
        print(f"The path '{file_path}' refers to a directory. Contents:")
        for item in response_data:
            print(f"- {item['name']} ({'directory' if item['type'] == 'dir' else 'file'})")
        print("Please specify a file path, not a directory.")
        return

    update_url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
    data = {
        "message": "Update file",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
        "sha": response_data["sha"]
    }
    
    response = requests.put(update_url, headers=HEADERS, json=data)
    if response.status_code in [200, 201]:
        print(f"File {file_path} updated successfully in branch {branch} of {owner}/{repo}.")
    else:
        print(f"Failed to update file. Status code: {response.status_code}")
        print(f"Response content: {response.text}")

def main():
    if not all([GITHUB_API_KEY, OWNER, REPO, FILE_PATH]):
        print("Error: Missing required environment variables. Please check your .env file.")
        return

    print(f"Using file path: {FILE_PATH}")

    if not check_repo_exists(OWNER, REPO):
        print(f"Repository {OWNER}/{REPO} does not exist. Creating it...")
        create_repo(OWNER, REPO)
    else:
        print(f"Repository {OWNER}/{REPO} exists.")

    if check_file_exists(OWNER, REPO, FILE_PATH):
        print(f"File {FILE_PATH} exists in {OWNER}/{REPO}. Creating a new feature branch...")
        new_branch = create_branch(OWNER, REPO, "main", "feature-update-file")
        if new_branch:
            new_content = "This is the updated content of the file."
            update_file_in_branch(OWNER, REPO, FILE_PATH, new_branch, new_content)
    else:
        print(f"File {FILE_PATH} does not exist in {OWNER}/{REPO}. Creating it...")
        initial_content = "This is the initial content of the file."
        create_file(OWNER, REPO, FILE_PATH, initial_content)

if __name__ == "__main__":
    main()