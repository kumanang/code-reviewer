import os
import google.generativeai as genai
import requests

# Load API key from GitHub Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("GITHUB_REF").split("/")[-1]

# Read the code changes (diff)
with open("changes.diff", "r") as file:
    code_diff = file.read()

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Generate review comments using Gemini
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content(f"""
You are an AI code reviewer. Review the following code diff and provide detailed feedback:
{code_diff}
""")

review_comments = response.text

# Print AI-generated comments
print("AI Review Comments:\n", review_comments)

# Post comments to GitHub PR
github_api_url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

data = {"body": review_comments}
print(f"data: {data}")

response = requests.post(github_api_url, headers=headers, json=data)

if response.status_code == 201:
    print("Comment posted successfully!")
else:
    print("Failed to post comment:", response.text)
