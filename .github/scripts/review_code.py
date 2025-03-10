import os
import json
import requests
import google.generativeai as genai

# Load API keys and GitHub environment variables
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")  # Ensure this matches workflow
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("GITHUB_EVENT_PATH")

# Extract PR number from GitHub event JSON
if PR_NUMBER:
    with open(PR_NUMBER, "r") as f:
        event_data = json.load(f)
        PR_NUMBER = event_data["number"]

# Read the code changes (diff)
diff_file = "changes.diff"
if not os.path.exists(diff_file) or os.stat(diff_file).st_size == 0:
    print("⚠️ No code changes detected. Exiting.")
    exit(0)

with open(diff_file, "r") as file:
    code_diff = file.read()

# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Generate review comments using Gemini AI
response = model.generate_content(f"""
You are an AI code reviewer. Review the following code diff and provide feedback on Formatting, Performance improvements, Security issues, Refactoring suggestions, Readability as structured JSON in this format:
[
  {{"file": "filename.py", "line": 10, "comment": "Suggestion text"}},
  {{"file": "another_file.py", "line": 20, "comment": "Another suggestion"}}
]
Only return the JSON array, no additional text.
{code_diff}
""")
# Parse AI response safely
try:
    review_comments = json.loads(response.text)
except json.JSONDecodeError as e:
    print(f"❌ Error parsing AI response: {str(e)}")
    review_comments = []

# Save AI-generated comments to a file
with open("ai_review_comments.json", "w") as f:
    json.dump(review_comments, f)

if review_comments:
    print(f"✅ AI-generated comments saved to ai_review_comments.json ({len(review_comments)} suggestions).")
else:
    print("⚠️ No AI review comments generated.")
