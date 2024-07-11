import os
import requests
from datetime import datetime, timedelta 
from dotenv import load_dotenv

load_dotenv()

# Get variables from environment
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
OWNER = os.getenv("Owner")
REPO = os.getenv("Repository")

# GitHub API base URL
BASE_URL = "https://api.github.com"
HEADERS = {"Authorization": f"token {GITHUB_API_KEY}"}

def list_open_pull_requests(owner, repo):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls?state=open"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        pull_requests = response.json()
        for pr in pull_requests:
            print(f"PR #{pr['number']}: {pr['title']} by {pr['user']['login']}")
        return pull_requests
    else:
        print(f"Failed to fetch pull requests. Status code: {response.status_code}")
        return None

def automatic_pr_review(owner, repo, pr_number):
    print(f"Reviewing PR #{pr_number}")
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch PR files. Status code: {response.status_code}")
        return

    files = response.json()
    issues = []

    for file in files:
        # Check file size (raise an issue if > 1MB)
        if file['changes'] > 1000000:
            issues.append(f"File {file['filename']} is too large ({file['changes']} bytes)")

        # Check naming conventions (assume we want lowercase with underscores)
        if not file['filename'].islower() or ' ' in file['filename']:
            issues.append(f"File {file['filename']} doesn't follow naming conventions")

        # Check for TODO comments
        if 'patch' in file and 'TODO' in file['patch']:
            issues.append(f"File {file['filename']} contains TODO comments")

    if issues:
        comment = "Automatic review found the following issues:\n"
        for issue in issues:
            comment += f"- {issue}\n"
        comment_on_pull_request(owner, repo, pr_number, comment)
        print("Review completed. Issues found and commented on the PR.")
    else:
        print("Review completed. No issues found.")

    return issues
    pass

def check_pr_status(owner, repo, pr_number):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/checks"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to fetch PR status. Status code: {response.status_code}")
        return None

    checks = response.json()['check_runs']
    
    status_summary = {
        'total': len(checks),
        'success': 0,
        'failure': 0,
        'neutral': 0,
        'pending': 0
    }

    for check in checks:
        if check['status'] == 'completed':
            if check['conclusion'] == 'success':
                status_summary['success'] += 1
            elif check['conclusion'] in ['failure', 'timed_out', 'cancelled']:
                status_summary['failure'] += 1
            else:
                status_summary['neutral'] += 1
        else:
            status_summary['pending'] += 1

    print(f"PR #{pr_number} Status Summary:")
    for status, count in status_summary.items():
        print(f"{status.capitalize()}: {count}")

    return status_summary
    pass

def merge_pull_request(owner, repo, pr_number):
    # First, check the PR status
    status_summary = check_pr_status(owner, repo, pr_number)
    
    if status_summary is None:
        print(f"Unable to merge PR #{pr_number} due to status check failure.")
        return False

    # Check if all checks have passed
    if status_summary['failure'] > 0 or status_summary['pending'] > 0:
        print(f"Cannot merge PR #{pr_number}. There are failing or pending checks.")
        return False

    # Check if the PR has been approved
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to fetch PR reviews. Status code: {response.status_code}")
        return False

    reviews = response.json()
    approved = any(review['state'] == 'APPROVED' for review in reviews)

    if not approved:
        print(f"Cannot merge PR #{pr_number}. It has not been approved.")
        return False

    # If we've made it this far, attempt to merge the PR
    merge_url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
    merge_data = {
        "merge_method": "merge"  # You can change this to "squash" or "rebase" if preferred
    }
    
    merge_response = requests.put(merge_url, headers=HEADERS, json=merge_data)
    
    if merge_response.status_code == 200:
        print(f"Successfully merged PR #{pr_number}")
        return True
    else:
        print(f"Failed to merge PR #{pr_number}. Status code: {merge_response.status_code}")
        print(f"Error message: {merge_response.json().get('message', 'No message provided')}")
        return False
    pass

def comment_on_pull_request(owner, repo, pr_number, comment):
    url = f"{BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    data = {"body": comment}
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"Comment added to PR #{pr_number}")
    else:
        print(f"Failed to add comment. Status code: {response.status_code}")
    pass

def update_pull_request(owner, repo, pr_number, title=None, body=None, state=None):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    
    # Prepare the data for the update
    update_data = {}
    if title is not None:
        update_data['title'] = title
    if body is not None:
        update_data['body'] = body
    if state is not None:
        if state not in ['open', 'closed']:
            print(f"Invalid state '{state}'. Must be 'open' or 'closed'.")
            return False
        update_data['state'] = state
    
    # If no updates are specified, inform the user and return
    if not update_data:
        print("No updates specified. Pull request remains unchanged.")
        return False
    
    # Send the PATCH request to update the pull request
    response = requests.patch(url, headers=HEADERS, json=update_data)
    
    if response.status_code == 200:
        print(f"Successfully updated PR #{pr_number}")
        updated_pr = response.json()
        print(f"New title: {updated_pr['title']}")
        print(f"New state: {updated_pr['state']}")
        return True
    else:
        print(f"Failed to update PR #{pr_number}. Status code: {response.status_code}")
        print(f"Error message: {response.json().get('message', 'No message provided')}")
        return False
    pass

from datetime import datetime
from collections import Counter

def pr_analytics(owner, repo, state='all', days=30):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls"
    params = {
        'state': state,
        'sort': 'updated',
        'direction': 'desc',
        'per_page': 100
    }
    
    all_prs = []
    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch PRs. Status code: {response.status_code}")
            return None
        
        prs = response.json()
        if not prs:
            break
        
        all_prs.extend(prs)
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break

    # Filter PRs updated within the last 'days' days
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_prs = [pr for pr in all_prs if datetime.strptime(pr['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > cutoff_date]

    if not recent_prs:
        print(f"No PRs updated in the last {days} days.")
        return None

    # Calculate analytics
    total_prs = len(recent_prs)
    merged_prs = [pr for pr in recent_prs if pr['merged_at']]
    open_prs = [pr for pr in recent_prs if pr['state'] == 'open']
    
    if merged_prs:
        avg_time_to_merge = sum((datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ') - 
                                 datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')).total_seconds() 
                                for pr in merged_prs) / len(merged_prs) / 3600  # in hours
    else:
        avg_time_to_merge = 0

    contributors = Counter(pr['user']['login'] for pr in recent_prs)
    top_contributors = contributors.most_common(5)

    # Fetch comments for each PR
    total_comments = 0
    for pr in recent_prs:
        comments_url = pr['comments_url']
        comments_response = requests.get(comments_url, headers=HEADERS)
        if comments_response.status_code == 200:
            total_comments += len(comments_response.json())

    avg_comments_per_pr = total_comments / total_prs if total_prs > 0 else 0

    # Print analytics
    print(f"\nPull Request Analytics for the last {days} days:")
    print(f"Total PRs: {total_prs}")
    print(f"Merged PRs: {len(merged_prs)}")
    print(f"Open PRs: {len(open_prs)}")
    print(f"Average time to merge: {avg_time_to_merge:.2f} hours")
    print(f"Average comments per PR: {avg_comments_per_pr:.2f}")
    print("\nTop Contributors:")
    for contributor, count in top_contributors:
        print(f"  {contributor}: {count} PRs")

    return {
        'total_prs': total_prs,
        'merged_prs': len(merged_prs),
        'open_prs': len(open_prs),
        'avg_time_to_merge': avg_time_to_merge,
        'avg_comments_per_pr': avg_comments_per_pr,
        'top_contributors': dict(top_contributors)
    }
    pass

def manage_pr_labels(owner, repo, pr_number, action='list', labels=None):
    url = f"{BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/labels"
    
    if action == 'list':
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            current_labels = [label['name'] for label in response.json()]
            print(f"Current labels for PR #{pr_number}:")
            for label in current_labels:
                print(f"- {label}")
            return current_labels
        else:
            print(f"Failed to fetch labels. Status code: {response.status_code}")
            return None

    elif action == 'add':
        if not labels:
            print("No labels specified to add.")
            return False
        response = requests.post(url, headers=HEADERS, json=labels)
        if response.status_code == 200:
            print(f"Successfully added label(s) to PR #{pr_number}")
            return True
        else:
            print(f"Failed to add label(s). Status code: {response.status_code}")
            return False

    elif action == 'remove':
        if not labels:
            print("No labels specified to remove.")
            return False
        for label in labels:
            delete_url = f"{url}/{label}"
            response = requests.delete(delete_url, headers=HEADERS)
            if response.status_code == 200:
                print(f"Successfully removed label '{label}' from PR #{pr_number}")
            else:
                print(f"Failed to remove label '{label}'. Status code: {response.status_code}")
        return True

    else:
        print(f"Invalid action '{action}'. Must be 'list', 'add', or 'remove'.")
        return False
    pass

def main():
    print("GitHub Pull Request Manager")
    print("==========================")

    while True:
        print("\nWhat would you like to do?")
        print("1. List open pull requests")
        print("2. Perform automatic PR review")
        print("3. Check PR status")
        print("4. Merge a pull request")
        print("5. Update a pull request")
        print("6. View PR analytics")
        print("7. Manage PR labels")
        print("8. Exit")

        choice = input("Enter your choice (1-8): ")

        if choice == '1':
            print("\nOpen Pull Requests:")
            prs = list_open_pull_requests(OWNER, REPO)
            for pr in prs:
                print(f"#{pr['number']} - {pr['title']}")

        elif choice == '2':
            pr_number = input("Enter the PR number to review: ")
            automatic_pr_review(OWNER, REPO, pr_number)

        elif choice == '3':
            pr_number = input("Enter the PR number to check status: ")
            check_pr_status(OWNER, REPO, pr_number)

        elif choice == '4':
            pr_number = input("Enter the PR number to merge: ")
            merge_pull_request(OWNER, REPO, pr_number)

        elif choice == '5':
            pr_number = input("Enter the PR number to update: ")
            title = input("Enter new title (press Enter to skip): ")
            body = input("Enter new body (press Enter to skip): ")
            state = input("Enter new state (open/closed, press Enter to skip): ")
            update_pull_request(OWNER, REPO, pr_number, 
                                title or None, 
                                body or None, 
                                state or None)

        elif choice == '6':
            days = int(input("Enter number of days for analytics (default 30): ") or 30)
            pr_analytics(OWNER, REPO, state='all', days=days)

        elif choice == '7':
            pr_number = input("Enter the PR number: ")
            action = input("What would you like to do with labels? (list/add/remove): ").lower()
            if action in ['add', 'remove']:
                labels = input("Enter label(s) separated by commas: ").split(',')
                labels = [label.strip() for label in labels]
                manage_pr_labels(OWNER, REPO, pr_number, action, labels)
            else:
                manage_pr_labels(OWNER, REPO, pr_number)

        elif choice == '8':
            print("Exiting the program. Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()