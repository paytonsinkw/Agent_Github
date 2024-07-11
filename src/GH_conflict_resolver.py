import os
import requests
from dotenv import load_dotenv
import base64
import time

load_dotenv()

# Get variables from this environment
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
OWNER = os.getenv("Owner")
REPO = os.getenv("Repository")

# GitHub API base URL
BASE_URL = "https://api.github.com"
HEADERS = {"Authorization": f"token {GITHUB_API_KEY}"}

def get_file_content(owner, repo, file_path, branch="main"):
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        content = base64.b64decode(response.json()["content"]).decode("utf-8")
        return content
    return None

def create_pull_request(owner, repo, base_branch, head_branch, title, body):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls"
    data = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch
    }
    response = requests.post(url, headers=HEADERS, json=data)
    return response.json() if response.status_code == 201 else None

def create_feature_branch(owner, repo, base_branch="main"):
    # Get the SHA of the latest commit on the base branch
    url = f"{BASE_URL}/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to get base branch info. Status code: {response.status_code}")
        return None
    
    sha = response.json()['object']['sha']
    
    # Create a new branch
    timestamp = int(time.time())
    new_branch_name = f"feature-branch-{timestamp}"
    url = f"{BASE_URL}/repos/{owner}/{repo}/git/refs"
    data = {
        "ref": f"refs/heads/{new_branch_name}",
        "sha": sha
    }
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"Created new branch: {new_branch_name}")
        return new_branch_name
    else:
        print(f"Failed to create new branch. Status code: {response.status_code}")
        return None

def check_repo_content(owner, repo):
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        contents = response.json()
        # Filter out .gitignore and README files
        significant_files = [file for file in contents if file['name'] not in ['.gitignore', 'README.md']]
        return len(significant_files) > 0
    return False

def analyze_conflicts(owner, repo, base_branch, head_branch):
    compare_url = f"{BASE_URL}/repos/{owner}/{repo}/compare/{base_branch}...{head_branch}"
    response = requests.get(compare_url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data["files"]  # This now includes all changed files with their status
    return None

def resolve_conflicts(owner, repo, file_path, base_content, head_content):
    # This is a very simple conflict resolution strategy
    # In a real-world scenario, you'd want a more sophisticated approach
    merged_content = f"<<<<<<< BASE\n{base_content}\n=======\n{head_content}\n>>>>>>> HEAD\n"
    return merged_content

def refactor_file(content, old_name, new_name):
    return content.replace(old_name, new_name)

def update_file_in_branch(owner, repo, file_path, branch, content, commit_message):
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
    
    # First, get the current file to obtain its SHA
    response = requests.get(url, headers=HEADERS, params={"ref": branch})
    if response.status_code == 200:
        current_file = response.json()
        sha = current_file["sha"]
    else:
        print(f"Failed to get current file. Status code: {response.status_code}")
        return False

    # Now, update the file
    data = {
        "message": commit_message,
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha,
        "branch": branch
    }
    response = requests.put(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"File {file_path} updated successfully in branch {branch}")
        return True
    else:
        print(f"Failed to update file. Status code: {response.status_code}")
        return False
    
def handle_added_file(owner, repo, file_path, branch):
    content = get_file_content(owner, repo, file_path, branch)
    return content  # This content should be added to the feature branch

def handle_removed_file(owner, repo, file_path, base_branch):
    content = get_file_content(owner, repo, file_path, base_branch)
    return f"# This file was deleted in the base branch. Please review.\n\n{content}"

def main():
    if not check_repo_content(OWNER, REPO):
        print("Repository is empty or contains only basic files. No action needed.")
        return

    base_branch = "main"
    new_feature_branch = create_feature_branch(OWNER, REPO, base_branch)
    if not new_feature_branch:
        print("Failed to create new feature branch. Exiting.")
        return

    changes = analyze_conflicts(OWNER, REPO, base_branch, new_feature_branch)
    if changes:
        for file in changes:
            if file["status"] == "modified":
                base_content = get_file_content(OWNER, REPO, file["filename"], base_branch)
                head_content = get_file_content(OWNER, REPO, file["filename"], new_feature_branch)
                if base_content and head_content:
                    merged_content = resolve_conflicts(OWNER, REPO, file["filename"], base_content, head_content)
                    success = update_file_in_branch(OWNER, REPO, file["filename"], new_feature_branch, merged_content, "Resolve conflicts")
            elif file["status"] == "added":
                new_content = handle_added_file(OWNER, REPO, file["filename"], base_branch)
                success = update_file_in_branch(OWNER, REPO, file["filename"], new_feature_branch, new_content, "Add new file")
            elif file["status"] == "removed":
                kept_content = handle_removed_file(OWNER, REPO, file["filename"], base_branch)
                success = update_file_in_branch(OWNER, REPO, file["filename"], new_feature_branch, kept_content, "Keep removed file for review")
            
            if not success:
                print(f"Failed to update {file['filename']}. Skipping this file.")

        # Create a pull request with the resolved conflicts
        pr = create_pull_request(OWNER, REPO, base_branch, new_feature_branch, "Resolve conflicts and handle changes", "Automated conflict resolution and change handling")
        if pr:
            print(f"Pull request created: {pr['html_url']}")
        else:
            print("Failed to create pull request")
    else:
        print("No changes found")

if __name__ == "__main__":
    main()