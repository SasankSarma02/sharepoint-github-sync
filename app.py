import os
import requests
import json
from flask import Flask, request
from msal import ConfidentialClientApplication

app = Flask(__name__)

# GitHub Webhook Secret (Set this when creating the webhook)
GITHUB_SECRET = "PdEEEM9eF5GlJK9Ms8lh0ag0QRaoBRYB"

# GitHub Configuration
GITHUB_PAT = "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"
GITHUB_OWNER = "DataSkateCOE"
GITHUB_REPO = "Sample"

# SharePoint Configuration
TENANT_ID = "a11bcc1d-8378-4456-9586-266a7e4159a5"
CLIENT_ID = "27acc87b-7b3b-4a5b-8619-c5c92c553004"
CLIENT_SECRET = "2s78Q~k.h4Y93yMHrhEN~AJDi9~WaNRO1ZecSciq"
SHAREPOINT_DRIVE_ID = "b!KylLN78sGkeCIslsx8s4ADTopHhbjbVGkHvJRN1I5kD_ok4-zZ2oS4OxwZDI_B26"

AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

# Authenticate with SharePoint using MSAL
def get_sharepoint_access_token():
    app = ConfidentialClientApplication(CLIENT_ID, CLIENT_SECRET, AUTHORITY_URL)
    token_response = app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" in token_response:
        return token_response["access_token"]
    else:
        raise Exception("Could not get access token:", token_response)

# Upload file to SharePoint
def upload_file_to_sharepoint(file_path, file_content, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    encoded_path = file_path.replace("/", "%2F")
    upload_url = f"{GRAPH_API_URL}/drives/{SHAREPOINT_DRIVE_ID}/root:/{encoded_path}:/content"
    
    response = requests.put(upload_url, headers=headers, data=file_content)
    
    if response.status_code in [200, 201]:
        print(f"Uploaded: {file_path}")
    else:
        print(f"Failed to upload {file_path}: {response.status_code}, {response.text}")

# Process GitHub webhook event
@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    data = request.json
    if "commits" not in data:
        return {"message": "No commits found"}, 400
    
    access_token = get_sharepoint_access_token()
    
    # Loop through each commit and sync new/updated files
    for commit in data["commits"]:
        for file_path in commit.get("added", []) + commit.get("modified", []):
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/{file_path}"
            file_content = requests.get(raw_url).content
            upload_file_to_sharepoint(file_path, file_content, access_token)

    return {"message": "Sync complete"}, 200
