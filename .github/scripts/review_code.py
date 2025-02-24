import os
import google.generativeai as genai
import requests

# Load API keys and GitHub environment variables
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
You are an AI code reviewer. Review the following code diff and provide feedback as structured JSON in this format:
[
  {{"file": "filename.py", "line": 10, "comment": "Suggestion text"}},
  {{"file": "another_file.py", "line": 20, "comment": "Another suggestion"}}
]
Only return the JSON array, no additional text.
{code_diff}
""")

# Extract AI review comments (assumed to be JSON)
try:
    review_comments = eval(response.text)  # Convert AI response to list
except Exception as e:
    print("❌ Error parsing AI response:", str(e))
    review_comments = []

# Function to post comments to GitHub PR
def post_pr_comment(file, line, comment):
    """Post an inline review comment on a GitHub pull request."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/comments"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "body": comment,
        "commit_id": os.getenv("GITHUB_SHA"),  # Ensure the comment is attached to the latest commit
        "path": file,
        "line": line,
        "side": "RIGHT"  # Comment on the right side (new changes)
    }
    
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"✅ Comment posted on {file} (Line {line}): {comment}")
    else:
        print(f"❌ Failed to post comment on {file} (Line {line}):", response.text)

# Post each AI-generated comment
if review_comments:
    print("✍️ Posting AI-generated comments on PR...")
    for review in review_comments:
        post_pr_comment(review["file"], review["line"], review["comment"])
else:
    print("⚠️ No AI review comments to post.")
