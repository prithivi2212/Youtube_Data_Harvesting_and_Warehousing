from googleapiclient.discovery import build
import pymongo
import streamlit as st
import pymysql
import datetime
import pandas as pd

st.set_page_config(page_title='My Streamlit App', page_icon=':bar_chart:', layout="wide")
pd.set_option('display.max_columns', None)

st.title(" :red[YouTube] :black[Data Harvesting and Warehousing, Using SQL, MongoDB & Streamlit]")

#Input field for API Key
api_key = st.text_input("Enter your YouTube API Key", type = "password")

if st.button("Submit API Key"):
     if api_key:
       st.success("Submitted your YouTube API key.")
     else:
        st.info("Please enter your YouTube API key.")

# Create a YouTube API client
youtube = build("youtube", "v3", developerKey=api_key)


# Connecting to MongoDB
uri = "mongodb+srv://prithivin22:Mongodb1@cluster0.aikv67f.mongodb.net/"  #(uri - Uniform Resource Identifier)
client = pymongo.MongoClient(uri)
mydb = client["Youtube_data_harvesting"]


# Connecting to MySQL
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Mysql@123",
    database="Youtube",
    port = 3306
    )
cursor =conn.cursor()

# Input field for channel ID
channel_id = st.text_input("Enter your channel Id")

# Function to retrieve channel data
def Retrieve_Channel_and_Video_Data(youtube, channel_id):
    channel_request = youtube.channels().list(
        part="snippet,contentDetails,statistics,status",
        id=channel_id
    )
    channel_response = channel_request.execute()
    
    # Initialize the data dictionary
    data = {}

    if "items" in channel_response and channel_response["items"]:
        channel_data = channel_response["items"][0]
        data["Channel"] = {
            "Channel_Id": channel_data["id"],
            "Channel_Name": channel_data["snippet"]["title"],
            "channel_type" : channel_data.get("brandingSettings", {}).get("channel", {}).get("type", ""),
            "Subscription_Count": channel_data["statistics"]["subscriberCount"],
            "Channel_Views": channel_data["statistics"]["viewCount"],
            "Channel_Description": channel_data["snippet"]["description"],
            "channel_status" : channel_data["status"]["privacyStatus"],
            "Video_count" : channel_data["statistics"]["videoCount"]  
            }

    # Retrieve video data for the max view count
    video_request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=10,
        order="viewCount"
    )
    video_response = video_request.execute()

    # Initialize a list to store data for multiple videos
    video_data_list = []

    # Function to convert duration from ISO 8601 format to HH:MM:SS format
    def convert_duration(duration):
        import re
        match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration)
        hours = int(match.group(1)[:-1]) if match.group(1) else 0
        minutes = int(match.group(2)[:-1]) if match.group(2) else 0
        seconds = int(match.group(3)[:-1]) if match.group(3) else 0
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    for video_item in video_response["items"]:
        video_id = video_item["id"]["videoId"]

        
        # Retrieve video data
        video_data_request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
        )
        video_data_response = video_data_request.execute()

        if "items" in video_data_response and video_data_response["items"]:
            video_data = video_data_response["items"][0]
            video_statistics = video_data.get("statistics", {})

        # Convert duration
        duration = convert_duration(video_data["contentDetails"]["duration"])

        # Convert publishedAt to datetime format
        published_at = datetime.datetime.strptime(video_data["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        formatted_published_at = published_at.strftime("%Y-%m-%d %H:%M:%S")

        # Retrieve comments for the video (first 2 comments)
        comments_request = youtube.commentThreads().list(
                  part="snippet",
                  videoId=video_data["id"], 
                  maxResults = 2 # Limit to the first 2 comments
                )
        comments_response = comments_request.execute()
        comments_data = []

        if "items" in comments_response:
            for comment_item in comments_response["items"]:
                comment_snippet = comment_item.get("snippet", {})
                comment_id = comment_item["id"]
                comment_text = comment_snippet.get("topLevelComment", {}).get("snippet", {}).get("textDisplay", "")
                comment_author = comment_snippet.get("topLevelComment", {}).get("snippet", {}).get("authorDisplayName", "")
                comment_publishedAt = comment_snippet.get("topLevelComment", {}).get("snippet", {}).get("publishedAt", "")

                # Convert comment_publishedAt to MySQL datetime format
                comment_publishedAt = datetime.datetime.strptime(comment_publishedAt, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")

                comments_data.append({
                    "comment_id": comment_id,
                    "Video_ID": video_id,
                    "comment_text": comment_text,
                    "comment_author": comment_author,
                    "comment_publishedAt": comment_publishedAt
               })
                            
        video_data = {
            "Video_ID": video_id,
            "Channel_ID": channel_data["id"],
            "Playlist_Id": channel_data["contentDetails"]["relatedPlaylists"]["uploads"],
            "Video_Name": video_data["snippet"]["title"],
            "Video_Description": video_data["snippet"]["description"],
            "Tags": video_data["snippet"].get("tags", []),
            "Published_At": formatted_published_at,
            "View Count": video_statistics.get("viewCount", 0),
            "Like_Count": video_statistics.get("likeCount", 0),
            "Dislike_Count": video_statistics.get("dislikeCount", 0),
            "Favorite_Count": video_statistics.get("favoriteCount", 0),
            "Comment_Count": video_statistics.get("commentCount", 0),
            "Duration": duration,
            "Thumbnail": video_data["snippet"]["thumbnails"]["default"]["url"],
            "Caption_Status": video_data["contentDetails"].get("caption", ""),
            "Comments": comments_data
        }
    
        video_data_list.append(video_data)

    # Store video data for both videos in your data dictionary
    data["Videos"] = video_data_list

    return data

# Retrieve and display channel and video data
if st.button("Retrieve Data"):
    retrieved_data = Retrieve_Channel_and_Video_Data(youtube, channel_id)
    
    if retrieved_data:
        st.write("Retrieved Data:")
        st.write(retrieved_data)


# Create a Streamlit dropdown menu for selecting what to store in MongoDB
data_to_store = st.selectbox("Select data to store in MongoDB", ["Channel Details", "Video Details", "Comment Details"])

if st.button("Store Selected Data in MongoDB"):
    if data_to_store == "Channel Details":
        # Call the function to retrieve channel data
        channel_data = Retrieve_Channel_and_Video_Data(youtube, channel_id)

        # Check if channel data was successfully retrieved
        if channel_data and "Channel" in channel_data:
            # Extract channel details
            channel_details = channel_data["Channel"]
            channel_collection = mydb["channel_details"]

            # Check if the channel details already exist in MongoDB
            existing_channel = channel_collection.find_one({"Channel_Id": channel_details["Channel_Id"]})
            
            if not existing_channel:
                # Insert the channel details into the MongoDB collection
                channel_collection.insert_one(channel_details)
                st.success("Channel details have been stored in MongoDB.")
            else:
                st.warning("Channel details with the same ID already exist in MongoDB. Skipping insertion.")
        else:
            st.error("Failed to retrieve channel details.")
    
    elif data_to_store == "Video Details":
        # Call the function to retrieve video data
        video_data = Retrieve_Channel_and_Video_Data(youtube, channel_id)

        # Check if video data was successfully retrieved
        if video_data and "Videos" in video_data:
            # Extract video details
            video_details = video_data["Videos"]
            video_collection = mydb["video_details"]

            for video_detail in video_details:
                #Check if the video details already exists in MongoDB collection
                existing_video = video_collection.find_one({"Channel_ID": video_detail["Channel_ID"]})

                if not existing_video:
                    # Insert the video details into the MongoDB collection
                    video_collection.insert_many(video_details)

                    st.success("Video details have been stored in MongoDB.")
                else:
                    st.warning("Video details with the same ID already exist in MongoDB. Skipping insertion")
        else:
            st.error("Failed to retrieve video details.")
    
    elif data_to_store == "Comment Details":
        # Call the function to retrieve video data
        video_data = Retrieve_Channel_and_Video_Data(youtube, channel_id)

        # Check if video data was successfully retrieved
        if video_data and "Videos" in video_data:
            # Extract comments data from the first video (modify as needed)
            comments_data = video_data["Videos"][0].get("Comments", [])
            comments_collection = mydb["comments"]
            
            for comment_data in comments_data:
                #Check if the comment details already exists in MongoDB collection
                existing_comments = comments_collection.find_one({"Video_ID": comment_data["Video_ID"]})

                if not existing_comments:
                    # Insert the comments data into the MongoDB collection
                    comments_collection.insert_many(comments_data)

                    st.success("Comments have been stored in MongoDB.")
                else:
                    st.warning("Comment details with the same ID already exist in MongoDB. Skipping insertion")
        else:
            st.error("Failed to retrieve video details.")


# Define SQL queries to create tables and their schemas
# SQL query to create the 'channel' table
create_channel_table = """
CREATE TABLE IF NOT EXISTS channel (
    Channel_Id VARCHAR(255) PRIMARY KEY,
    Channel_Name VARCHAR(255),
    channel_type VARCHAR(255),
    Subscription_Count INT,
    Channel_Views INT,
    Channel_Description TEXT,
    channel_status VARCHAR(255),
    Video_count INT
)
"""
# SQL query to create the 'video' table
create_video_table = """
CREATE TABLE IF NOT EXISTS video (
    Video_ID VARCHAR(255) PRIMARY KEY,
    Channel_ID VARCHAR(255),
    Playlist_Id VARCHAR(255),
    Video_Name VARCHAR(255),
    Video_Description TEXT,
    Published_At DATETIME,
    View_Count INT,
    Like_Count INT,
    Dislike_Count INT,
    Favorite_Count INT,
    Comment_Count INT,
    Duration TIME,
    Thumbnail VARCHAR(255),
    Caption_Status VARCHAR(255),
    FOREIGN KEY (Channel_ID) REFERENCES channel(Channel_Id)
)
"""
# SQL query to create the 'comment' table
create_comment_table = """
CREATE TABLE IF NOT EXISTS comment (
    comment_id VARCHAR(255) PRIMARY KEY,
    Video_ID VARCHAR(255),
    comment_text TEXT,
    comment_author VARCHAR(255),
    comment_publishedAt DATETIME,
    FOREIGN KEY (Video_ID) REFERENCES video(Video_ID)
)
"""
# Execute the SQL queries to create tables
cursor.execute(create_channel_table)
cursor.execute(create_video_table)
cursor.execute(create_comment_table)

# Commit the changes to the MySQL database
conn.commit()

# Function to fetch all channel names from MongoDB
def fetch_channel_names_from_mongo():
    channel_collection = mydb["channel_details"]
    channel_names = channel_collection.distinct("Channel_Name")
    return channel_names

# Input field for selecting a channel name
selected_channel = st.selectbox("Select a Channel", fetch_channel_names_from_mongo())

if st.button("Submit"):
    if selected_channel:
        data_to_migrate = st.selectbox("Select data to migrate to MySQL", ["Channel Details", "Video Details", "Comments"])

        if st.button("Migrate Selected Data from MongoDB to MySQL"):
            if data_to_migrate == "Channel Details":
                # Connect to the MongoDB collection
                mongo_channel_collection = mydb["channel_details"]

                # Fetch all channel documents from MongoDB
                mongo_channel_data = list(mongo_channel_collection.find())

                if mongo_channel_data:
                    # Iterate through MongoDB channel data and insert into MySQL
                    for channel_document in mongo_channel_data:
                        # Define the SQL query to insert channel data into MySQL
                        sql_insert_channel = """
                        INSERT IGNORE INTO channel (
                            Channel_Id, Channel_Name, channel_type, Subscription_Count, 
                            Channel_Views, Channel_Description, channel_status, Video_count
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """

                        # Extract data from the MongoDB document
                        channel_values = (
                            channel_document["Channel_Id"],
                            channel_document["Channel_Name"],
                            channel_document["channel_type"],
                            channel_document["Subscription_Count"],
                            channel_document["Channel_Views"],
                            channel_document["Channel_Description"],
                            channel_document["channel_status"],
                            channel_document["Video_count"]
                        )

                        # Execute the SQL insert query
                        cursor.execute(sql_insert_channel, channel_values)

                    # Commit the changes to the MySQL database
                    conn.commit()

                    st.success("Channel details have been migrated from MongoDB to MySQL.")
                else:
                    st.error("No channel details found in MongoDB.")
            elif data_to_migrate == "Video Details":
                # Connect to the MongoDB collection
                mongo_video_collection = mydb["video_details"]

                # Fetch all video documents from MongoDB
                mongo_video_data = list(mongo_video_collection.find())

                if mongo_video_data:
                    # Iterate through MongoDB video data and insert into MySQL
                    for video_document in mongo_video_data:
                        # Define the SQL query to insert video data into MySQL
                        sql_insert_video = """
                        INSERT IGNORE INTO video (
                            Channel_ID, Video_ID, Playlist_Id, Video_Name, Video_Description, 
                            Published_At, View_Count, Like_Count, Dislike_Count, 
                            Favorite_Count, Comment_Count, Duration, Thumbnail, Caption_Status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        # Extract data from the MongoDB document
                        video_values = (
                            video_document["Channel_ID"],
                            video_document["Video_ID"],
                            video_document["Playlist_Id"],
                            video_document["Video_Name"],
                            video_document["Video_Description"],
                            video_document["Published_At"],
                            video_document["View Count"],
                            video_document["Like_Count"],
                            video_document["Dislike_Count"],
                            video_document["Favorite_Count"],
                            video_document["Comment_Count"],
                            video_document["Duration"],
                            video_document["Thumbnail"],
                            video_document["Caption_Status"]
                        )

                        # Execute the SQL insert query
                        cursor.execute(sql_insert_video, video_values)

                    # Commit the changes to the MySQL database
                    conn.commit()

                    st.success("Video details have been migrated from MongoDB to MySQL.")
                else:
                    st.error("No video details found in MongoDB.")
            elif data_to_migrate == "Comments":
                # Connect to the MongoDB collection
                mongo_comments_collection = mydb["comments"]

                # Fetch all comments documents from MongoDB
                mongo_comments_data = list(mongo_comments_collection.find())

                if mongo_comments_data:
                    # Iterate through MongoDB comments data and insert into MySQL
                    for comment_document in mongo_comments_data:
                        # Define the SQL query to insert comment data into MySQL
                        sql_insert_comment = """
                        INSERT IGNORE INTO comment (
                            comment_id, Video_ID, comment_text, comment_author, comment_publishedAt
                        ) VALUES (%s, %s, %s, %s, %s)
                        """

                        # Extract data from the MongoDB document
                        comment_values = (
                            comment_document["comment_id"],
                            comment_document["Video_ID"],
                            comment_document["comment_text"],
                            comment_document["comment_author"],
                            comment_document["comment_publishedAt"]
                        )

                        # Execute the SQL insert query
                        cursor.execute(sql_insert_comment, comment_values)

                    # Commit the changes to the MySQL database
                    conn.commit()

                    st.success("Comments have been migrated from MongoDB to MySQL.")
                else:
                    st.error("No comments found in MongoDB.")
            st.success(f"Data for {selected_channel} has been migrated from MongoDB to MySQL.")
    else:
        st.warning("Please select a Channel")

# Map questions to SQL queries
sql_queries = {
    "1.What are the names of all the videos and their corresponding channels?":
        "SELECT Video_Name, Channel_Name FROM youtube.video INNER JOIN youtube.channel ON video.channel_id = channel.channel_id order by Channel_Name",
    
    "2.Which channels have the most number of videos, and how many videos do they have?":
        "SELECT Channel_Name, Video_count from youtube.channel order by Video_count DESC LIMIT 1",
    
    "3.What are the top 10 most viewed videos and their respective channels?":
        "SELECT v.Video_Name, c.Channel_Name, v.View_Count FROM video v INNER JOIN channel c ON v.Channel_Id = c.Channel_Id ORDER BY v.View_Count DESC LIMIT 10",
    
    "4.How many comments were made on each video, and what are their corresponding video names?":
        "SELECT Video_Name, Comment_Count FROM youtube.video ORDER BY Comment_Count",
    
    "5.Which videos have the highest number of likes, and what are their corresponding channel names?":
        "SELECT Video_Name, Channel_Name, Like_Count FROM youtube.video INNER JOIN youtube.channel ON channel.Channel_ID = video.Channel_ID ORDER BY Like_Count DESC LIMIT 1",
    
    "6.What is the total number of likes and dislikes for each video, and what are their corresponding video names?":
        "SELECT Video_Name, Like_Count, Dislike_Count FROM youtube.video ORDER BY Like_Count",
    
    "7.What is the total number of views for each channel, and what are their corresponding channel names?":
        "SELECT Channel_Name, Channel_Views AS Total_Views FROM youtube.channel ORDER BY Channel_Name",
    
    "8.What are the names of all the channels that have published videos in the year 2022?":
        "SELECT DISTINCT Channel_Name FROM youtube.channel INNER JOIN youtube.video ON channel.Channel_Id = video.Channel_ID WHERE YEAR (video.Published_At) = 2022",
    
    "9.What is the average duration of all videos in each channel, and what are their corresponding channel names?":
        "SELECT Channel_Name, TIME_FORMAT(sec_to_time(AVG(TIME_TO_SEC(Duration))), '%H:%i:%s') AS Average_Duration FROM youtube.channel INNER JOIN youtube.video ON channel.Channel_Id = video.Channel_ID GROUP BY Channel_Name ORDER BY Channel_Name",
    
    "10.Which videos have the highest number of comments, and what are their corresponding channel names?":
        "SELECT Channel_Name, Comment_Count FROM youtube.channel INNER JOIN youtube.video ON channel.Channel_ID = video.Channel_ID ORDER BY Comment_Count DESC LIMIT 1"
}

# Get the SQL query corresponding to the selected question
selected_query = st.selectbox("Select your Query", list(sql_queries.keys()))

if st.button("Fetch Data"):
    try:
        # Execute the selected SQL query
        cursor.execute(sql_queries[selected_query])
        
        # Fetch the data from the executed query
        query_result = cursor.fetchall()
        
        if query_result:
            # Convert the result to a DataFrame for easy display
            df = pd.DataFrame(query_result, columns=[i[0] for i in cursor.description])
            
            # Display the DataFrame as a table
            st.write("Query Result:")
            df.index = df.index + 1
            st.dataframe(df)
        else:
            st.warning("No data found for the selected query.")
    except Exception as e:
        st.error(f"An error occurred while executing the query: {str(e)}")