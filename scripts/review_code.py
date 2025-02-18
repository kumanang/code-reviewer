import os
import openai
import requests

# Load API key from GitHub Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Read code changes
with open("changes.diff", "r") as file:
    code_diff = file.read()

# Call OpenAI GPT to analyze the code
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an AI code reviewer. Analyze the given code diff and suggest improvements."},
        {"role": "user", "content": code_diff},
    ],
)

review_comments = response["choices"][0]["message"]["content"]

# Print review comments
print("AI Review Comments:\n", review_comments)

# Post comments to GitHub PR
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("GITHUB_REF").split("/")[-1]

github_api_url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

data = {"body": review_comments}

response = requests.post(github_api_url, headers=headers, json=data)

if response.status_code == 201:
    print("Comment posted successfully!")
else:
    print("Failed to post comment:", response.text)
