import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import streamlit as st

def app():
    # Load environment variables from .env file
    load_dotenv('../.env/.env')

    # Retrieve database connection details from environment variables
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    table_name = 'xdr_data'

    # Create the connection string
    connection_string = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    engine = create_engine(connection_string)

    # Query the data
    query = 'SELECT * FROM xdr_data'
    data = pd.read_sql(query, engine)

    # Display the data in Streamlit
    st.title("User Overview Analysis")
    st.write(data.head())

    # Handling Missing Values
    numeric_columns = data.select_dtypes(include=['float64']).columns
    text_columns = data.select_dtypes(include=['object']).columns
    data_cleaned = data.copy()
    data_cleaned[numeric_columns] = data[numeric_columns].fillna(data[numeric_columns].mean())
    data_cleaned[text_columns] = data[text_columns].fillna('N/A')
    data_cleaned = data_cleaned.dropna(subset=['MSISDN/Number'])

    st.subheader("Cleaned Data Summary")
    st.write(data_cleaned.info())

    # Identify the top 10 handsets used by the customers
    top_10_handsets = data['Handset Type'].value_counts().head(10)
    st.subheader("Top 10 Handsets")
    st.bar_chart(top_10_handsets)

    # Identify the top 3 handset manufacturers
    top_3_manufacturers = data['Handset Manufacturer'].value_counts().head(3)
    st.subheader("Top 3 Handset Manufacturers")
    st.write(top_3_manufacturers)

    # Identify the top 5 handsets per top 3 handset manufacturer
    manufacturer_data = {}
    for manufacturer in top_3_manufacturers.index:
        top_5_handsets = data[data['Handset Manufacturer'] == manufacturer]['Handset Type'].value_counts().head(5)
        manufacturer_data[manufacturer] = top_5_handsets

    for manufacturer, handsets in manufacturer_data.items():
        st.subheader(f"Top 5 Handsets for Manufacturer {manufacturer}")
        st.write(handsets)

    # Group by each user
    dl_columns = ['Social Media DL (Bytes)', 'Google DL (Bytes)', 'Email DL (Bytes)',
                  'Youtube DL (Bytes)', 'Netflix DL (Bytes)', 'Gaming DL (Bytes)', 'Other DL (Bytes)']
    ul_columns = ['Social Media UL (Bytes)', 'Google UL (Bytes)', 'Email UL (Bytes)',
                  'Youtube UL (Bytes)', 'Netflix UL (Bytes)', 'Gaming UL (Bytes)', 'Other UL (Bytes)']

    user_overview = data.groupby('MSISDN/Number').agg(
        xdr_sessions=('Dur. (ms)', 'count'),
        total_duration=('Dur. (ms)', 'sum'),
        **{col: (col, 'sum') for col in dl_columns},
        **{col: (col, 'sum') for col in ul_columns}
    ).reset_index()

    user_overview['total_dl_data'] = user_overview[dl_columns].sum(axis=1)
    user_overview['total_ul_data'] = user_overview[ul_columns].sum(axis=1)
    user_overview['total_data_volume'] = user_overview[dl_columns].sum(axis=1) + user_overview[ul_columns].sum(axis=1)
    user_overview = user_overview.drop(columns=dl_columns + ul_columns)

    st.subheader("User Overview")
    st.write(user_overview.head())

    # Exploratory Data Analysis (EDA)
    st.subheader("Data Description")
    st.write(data.describe())

    # Histograms
    st.subheader("Histograms of Duration and Total Data")
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    data[['Dur. (ms)', 'total_data']].hist(bins=30, ax=ax)
    st.pyplot(fig)

    # Scatter plot
    st.subheader("Scatter Plot of Duration vs Total Data")
    sns.scatterplot(x='Dur. (ms)', y='total_data', data=data)
    st.pyplot()

    # PCA
    st.subheader("PCA of Total Data and Duration")
    pca = PCA(n_components=2)
    principal_components = pca.fit_transform(data[['total_data', 'Dur. (ms)']])
    plt.scatter(principal_components[:, 0], principal_components[:, 1])
    plt.title('PCA of Total Data and Duration')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    st.pyplot()

# Note: Ensure to call this function in your main app script.