# Inspiration

The ongoing debate between Xbox and PlayStation enthusiasts is a prominent topic in the gaming community. Understanding the sentiment trends surrounding these two consoles can provide valuable insights for gamers, developers, and marketers. More info on the project can be found on: [Devpost](https://devpost.com/software/twitter-sentiment-analysis-sc4w1x) and its [demo here](https://youtu.be/uzoU234xk8A?si=ggFqIEqh1PnP2NL3).

## What It Does

This application analyzes Reddit discussions to gauge the sentiment towards Xbox and PlayStation over time. It retrieves relevant Reddit comments, processes them to determine sentiment scores, and visualizes the results in a time-series line graph, updated every 24 hours.

## How We Built It

- **Data Collection**: Utilized the Python Reddit API Wrapper (**PRAW**) to fetch comments mentioning Xbox and PlayStation from Reddit.
- **Data Ingestion**: Employed **Azure Event Hubs** to handle the streaming data from the Python script, directing the raw data into an Azure Storage Blob container.
- **Data Processing**: Leveraged **Microsoft Fabric Real-time Analytics** to ingest data from Azure Event Hubs into a KQL Database.
- **Deployment**: Deployed the Python script to **Azure Function Apps**, with credentials securely stored in **Azure Key Vault**.
- **Continuous Integration**: Enabled manual deployment using the VS Code Azure extension for seamless updates to the Azure Function App.
- **Security**: Configured Azure Key Vault's Role-Based Access Control (RBAC) to allow Azure Functions to read necessary credentials.
- **Data Analysis**: Aggregated Reddit comments into text blobs and utilized **Azure Cognitive Services Language** for sentiment analysis.
- **Data Visualization**: Created a real-time line chart displaying sentiment scores over time for both Xbox and PlayStation.

## Challenges We Ran Into

- **Deployment Issues**: Encountered failures in manual deployment via VS Code when pushing to GitHub, necessitating adjustments to the deployment workflow.
- **Data Ingestion**: Faced challenges in modifying the KQL database schema to accommodate streaming data, which required deleting and recreating tables with automatic schema matching.
- **Data Erasure**: Learned to effectively erase data from tables using Kusto Query Language (KQL).

## Accomplishments That We're Proud Of

- Successfully integrated multiple Azure services to create a cohesive data pipeline.
- Achieved real-time sentiment analysis with a 24-hour update cycle.
- Developed a user-friendly visualization tool to track sentiment trends over time.

## What We Learned

- Gained proficiency in deploying Python applications using Azure Function Apps and managing credentials with Azure Key Vault.
- Enhanced understanding of data ingestion and processing using Azure Event Hubs and Microsoft Fabric Real-time Analytics.
- Improved skills in data visualization and real-time analytics.

## What's Next for Reddit Sentiment Analysis

- **Expand Data Sources**: Incorporate additional social media platforms to provide a more comprehensive sentiment analysis.
- **Enhance Visualization**: Develop more interactive and detailed visualizations to better represent sentiment trends.
- **Optimize Performance**: Improve the efficiency of data processing and analysis to handle larger datasets and provide faster insights.
