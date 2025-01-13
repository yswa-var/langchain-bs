import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import dotenv as dotenv

ps = dotenv.dotenv_values()
# GitHub API settings
GITHUB_TOKEN = ps['GIT_TOKEN']
REPO_OWNER = "hyprbots"
REPO_NAME = "engineering-backlog"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

# Fetch Issues
@st.cache
def fetch_issues():
    issues = []
    page = 1
    while True:
        response = requests.get(BASE_URL, headers=headers, params={"state": "all", "page": page})
        if response.status_code != 200 or not response.json():
            break
        issues.extend(response.json())
        page += 1
    return issues

# Streamlit UI
st.title("GitHub Issues Dashboard")

issues = fetch_issues()
st.write(f"Total Issues Fetched: {len(issues)}")

# Group Tags
tags = {}
for issue in issues:
    for word in issue['title'].split():
        tags[word.lower()] = tags.get(word.lower(), 0) + 1

st.subheader("Tags Grouped")
st.bar_chart(pd.Series(tags).sort_values(ascending=False).head(10))

# Opened/Closed/Reopened Issues
opened = len([issue for issue in issues if issue['state'] == 'open'])
closed = len([issue for issue in issues if issue['state'] == 'closed'])
st.write(f"Opened: {opened}, Closed: {closed}")

# Oldest/Newest Bugs
oldest = min(issues, key=lambda x: x['created_at'])
newest = max(issues, key=lambda x: x['created_at'])
st.write(f"Oldest Issue: {oldest['title']} created at {oldest['created_at']}")
st.write(f"Newest Issue: {newest['title']} created at {newest['created_at']}")

# Unassigned/Long-Assigned Issues
unassigned = [issue for issue in issues if not issue['assignee']]
st.write(f"Unassigned Issues: {len(unassigned)}")
