# Youtube_Data_Harvesting_and_Warehousing

**Introduction**

This project develops a Streamlit app which uses Youtube API to retrieve Channel, Video & Comments data and stores them in MongoDB Database which is then migrated to SQL and used for queries in Streamlit.

**Contents**
- Technical Skills
- Installations
- Project Overview
- Working with the Project
- Updates
- License
- Contact
 
**Technical Skills**
1. Python & it's Library
2. API Integration
3. Structured Query Language(SQL)
4. Data management Using MongoDB Atlas
5. Streamlit

**Installations**

Install the following packages to run this project,
```python
pip install google-api-python-client
pip install streamlit
pip install pymongo
pip install pymysql
pip install datetime
pip install pandas
```

**Project Overview**

  This Project uses the python to install required libraries and create a Streamlit App. This App displays the Project title and a input box for YouTube API key. When entering the API key and submitted the input box for Channel ID displays. On entering the Channel ID and clicking the retrieve data it displays the channels data along with the top 10 viewed videos data and it's comments in json format.The selectbox to store data to MongoDB consists of Channel Details, Video Details, Comments Details in it, when anyone of these are selected it then transfer the data to MongoDB. The next selectbox contains the channel names, on selecting the channel name an another selectbox displays showing channel details, video details, comments details when clicking on this it migrates the the respective channel's details to the SQL table from the MongoDB database. Atlast the Ten questions are put in a selectbox which queries the SQL tables and displays the result in a DataFrame using pandas.

  **Working with the Project**

1. Clone the repository: ```git clone https://github.com/prithivi2212/Youtube_Data_Harvesting_and_Warehousing.git```
2. Install the required packages: ```pip install -r requirements.txt```
3. Run the Streamlit app: ```streamlit run app.py```
4. Access the app in your browser at ```http://localhost:8501```

**Updates**

Feel free to update me with a pull request if you encounter a problem or error with the code provided.

**License**

This project is licensed under the MIT License. Please review the LICENSE file for more details.

**Contact**

For further enquires reach out to me using,

📧 Email: prithivi.n22@gmail.com

🌐 LinkedIn: www.linkedin.com/in/prithivinanjundan






