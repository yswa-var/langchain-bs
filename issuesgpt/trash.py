import ast
import pandas as pd
import requests
from dotenv import dotenv_values
from tqdm import tqdm
from datetime import datetime
import pytz
from rich.console import Console
from rich.table import Table

# Load environment variables
setting = dotenv_values()
GITHUB_TOKEN = setting['GIT_TOKEN']
REPO_OWNER = "hyprbots"
REPO_NAME = "engineering-backlog"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

console = Console()

def fetch_issues():
    issues = []
    page = 1
    with tqdm(total=100, desc="Fetching Issues", unit="page") as pbar:
        while True:
            response = requests.get(BASE_URL, headers=headers, params={"state": "all", "page": page})
            if response.status_code != 200 or not response.json():
                break
            issues.extend(response.json())
            page += 1
            pbar.update(1)
            pbar.total = page + 100
            pbar.refresh()
    return issues

def transform_url(api_url):
    try:
        return api_url.replace("https://api.github.com/repos/", "https://github.com/").replace("/issues/", "/issues/")
    except AttributeError:
        return api_url

def extract_user_info(data, key):
    return data.apply(lambda x: ast.literal_eval(x).get(key) if pd.notna(x) and isinstance(ast.literal_eval(x), dict) else None)

def ensure_utc_timezone(dt):
    if pd.notna(dt):
        if dt.tzinfo is None:
            return dt.tz_localize('UTC')
        return dt.tz_convert('UTC')
    return dt

# Fetch issues and process DataFrame
issues = fetch_issues()
df = pd.DataFrame(issues)
columns_to_keep = [
    "url", "number", "title", "user", "labels", "state", "assignee", "comments",
    "created_at", "updated_at", "closed_at"
]
df = df[columns_to_keep]
df["url"] = df["url"].apply(transform_url)
df['user'] = extract_user_info(df['user'], "login")
df['assignee'] = extract_user_info(df['assignee'], "login")
df['labels'] = df['labels'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) else [])
df['labels_name'] = df['labels'].apply(lambda x: [d['name'] for d in x] if isinstance(x, list) else [])
df['labels_description'] = df['labels'].apply(lambda x: [d['description'] for d in x] if isinstance(x, list) else [])
df.drop('labels', axis=1, inplace=True)
df['created_at'] = pd.to_datetime(df['created_at'])
df['updated_at'] = pd.to_datetime(df['updated_at'])
df['closed_at'] = pd.to_datetime(df['closed_at'])
df['created_at'] = df['created_at'].apply(ensure_utc_timezone)
df['updated_at'] = df['updated_at'].apply(ensure_utc_timezone)
df['closed_at'] = df['closed_at'].apply(ensure_utc_timezone)
current_date = datetime.now(pytz.UTC)
df['age'] = (current_date - df['created_at']).dt.days
df = df[df['closed_at'].isna()]
df.drop('closed_at', axis=1, inplace=True)

def display_issues(df):
    table = Table(title="GitHub Issues")

    table.add_column("Number", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("User", style="green")
    table.add_column("Assignee", style="yellow")
    table.add_column("Comments", justify="right", style="blue")
    table.add_column("Created At", style="bold")
    table.add_column("Age (days)", justify="right", style="red")

    for _, row in df.iterrows():
        table.add_row(
            str(row['number']),
            row['title'],
            row['user'] if row['user'] else "N/A",
            row['assignee'] if row['assignee'] else "N/A",
            str(row['comments']),
            row['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
            str(row['age'])
        )

    console.print(table)

def query_issues(df, user=None, assignee=None, max_age=None):
    query_df = df.copy()
    if user:
        query_df = query_df[query_df['user'] == user]
    if assignee:
        query_df = query_df[query_df['assignee'] == assignee]
    if max_age:
        query_df = query_df[query_df['age'] <= max_age]

    display_issues(query_df)

# Example usage: Querying issues
query_issues(df, user="yashaswa-beepboop", max_age=30)
