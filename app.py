import streamlit as st
import snscrape.modules.twitter as sntwitter
from datetime import datetime, timedelta
import pytz
import pandas as pd
import re


st.set_page_config(layout="wide") 


@st.cache_data(ttl=60*60*24)  # Cache the results for 24 hours
def get_twitter_data(username):
    tweet_data = []

    # Get the current date and time
    now = datetime.now(pytz.utc)

    # Calculate the time 24 hours ago
    last_week = now - timedelta(days=7)

    # Scrape the tweets from the user
    for i, tweet in enumerate(sntwitter.TwitterUserScraper(username).get_items()):
        # Check if the tweet was posted within the last 24 hours
        if tweet.date > last_week:
            content = tweet.content

            # Extract the description, background, location, website, and LinkedIn URL
            founder = re.search(r'^\s*🔎([^“”"]+?)(?: is now building| comes out of stealth mode)', content, re.MULTILINE)
            background = re.search(r'Background:(.*?)\n', content)
            location = re.search(r'Location:(.*?)\n', content)
            description = re.search(r'(?:is now building| comes out of stealth mode)[\s\S]*?[\n\r]+([\s\S]*?)\n\nLocation:', content)
            website = re.search(r'(https://t.co/\S+)', content)
            linkedin = re.search(r'Connect on LinkedIn:\s*(https?://\S+)', content)

            # Check if the website URL and LinkedIn URL are the same
            if website and linkedin and website.group(1) == linkedin.group(1):
                website_url = None
                is_stealth = 'Yes'
            else:
                website_url = website.group(1) if website else None
                is_stealth = 'No'

            # Add the extracted information to the tweet_data list
            tweet_data.append({
                'date': tweet.date,
                'stealth': is_stealth,
                'founder': founder.group(1).strip() if founder else None,
                'background': background.group(1).strip() if background else None,
                'location': location.group(1).strip() if location else None,
                'description': None if not description or description.group(1).strip().startswith("Background:") else description.group(1).strip(),
                'website': website_url,
                'linkedin': linkedin.group(1).strip() if linkedin else None,
                
            })
        else:
            # Stop iterating if the tweet is older than one week
            break

    # Create a DataFrame from the tweet_data list
    df = pd.DataFrame(tweet_data)

    df['date'] = df['date'].dt.tz_convert(None)

    return df

def filter_dataframe(df, location, is_stealth):
    if location:
        df = df[df["location"].str.contains(location, case=False, na=False)]
    if is_stealth:
        df = df[df["stealth"].str.contains(is_stealth, case=False, na=False)]
    return df

st.title("Twitter Data Scraper")
username = "StealthCoSpy"
df = get_twitter_data(username)

st.sidebar.title("Filter Options")
location = st.sidebar.text_input("Location", value="")
is_stealth = st.sidebar.text_input("Stealth (Yes/No)", value="")

filtered_df = filter_dataframe(df, location, )
st.write(filtered_df)
