import streamlit as st
import pandas as pd
import os
from io import BytesIO
import charset_normalizer as chardet
import plotly.express as px

# Set up the app
st.set_page_config(page_title="Data Sweeper", layout='wide')
st.title("Data Sweeper")
st.write("Transform your files between CSV and Excel formats with built-in data cleaning and visualization")

# File uploader
uploaded_files = st.file_uploader("Upload your files (CSV or Excel):", type=["csv", "xlsx"], accept_multiple_files=True)

def detect_encoding(file):
    """Detect encoding using chardet"""
    raw_data = file.read(10000)  # Read first 10k bytes for encoding detection
    result = chardet.detect(raw_data)  # Detect encoding using chardet
    encoding = result['encoding']
    file.seek(0)  # Reset file pointer after reading for detection
    return encoding

def read_csv_with_encoding(file):
    """Read CSV with detected encoding"""
    encoding = detect_encoding(file)  # Detect the encoding
    try:
        return pd.read_csv(file, encoding=encoding)
    except UnicodeDecodeError:
        st.error(f"Unicode error while reading the file with encoding {encoding}. Trying with fallback encodings...")
        return read_csv_fallback(file)

def read_csv_fallback(file):
    """Fallback to other common encodings if the default encoding fails"""
    encodings = ['latin1', 'ISO-8859-1', 'windows-1252']
    for enc in encodings:
        try:
            return pd.read_csv(file, encoding=enc)
        except UnicodeDecodeError:
            continue
    st.error("All encoding attempts failed. Unable to read the CSV file.")
    return None

if uploaded_files:
    for file in uploaded_files:
        file_ext = os.path.splitext(file.name)[-1].lower()

        # Read the file based on its extension and handle encoding issues
        if file_ext == ".csv":
            df = read_csv_with_encoding(file)
            if df is None:
                continue  # Skip this file if it fails to read
        elif file_ext == ".xlsx":
            try:
                df = pd.read_excel(file)
            except Exception as e:
                st.error(f"Error reading the Excel file: {e}")
                continue
        else:
            st.error(f"Unsupported file type: {file_ext}")
            continue

        # Display file info
        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024} KB")

        # Show preview of the DataFrame
        st.write("Preview the Head of the Dataframe")
        st.dataframe(df.head())

        # Data cleaning options
        st.subheader("Data Cleaning Options")
        if st.checkbox(f"Clean Data for {file.name}"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Remove Duplicates from {file.name}"):
                    df.drop_duplicates(inplace=True)
                    st.write("Duplicates Removed!")

            with col2:
                if st.button(f"Fill Missing Values for {file.name}"):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                    st.write("Missing Values have been Filled")

            # Choose specific columns to keep or convert
            st.subheader("Select Columns to Convert")
            columns = st.multiselect(f"Choose Columns for {file.name}", df.columns, default=df.columns)
            df = df[columns]

            # Data visualizations
            st.subheader("Data Visualizations")
            if st.checkbox(f"Show Visualizations for {file.name}"):


             # Bar Chart Visualization
                st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])

            # Pie Chart Option
                pie_column = st.selectbox("Choose a column for the Pie Chart", df.columns)
                if pie_column:
                    pie_chart_data = df[pie_column].value_counts().reset_index()
                    pie_chart_data.columns = [pie_column, "Count"]

                    fig = px.pie(pie_chart_data, names=pie_column, values="Count", title=f"Pie Chart of {pie_column}") # type: ignore
                    st.plotly_chart(fig)


            # Conversion options
            st.subheader("Conversion Options")
            conversion_type = st.radio(f"Convert {file.name} to:", ["CSV", "Excel"], key=file.name)

            buffer = BytesIO()
            file_name = None
            mime_type = None

            if st.button(f"Convert {file.name}"):
                if conversion_type == "CSV":
                    df.to_csv(buffer, index=False)
                    file_name = file.name.replace(file_ext, ".csv")
                    mime_type = "text/csv"
                elif conversion_type == "Excel":
                    df.to_excel(buffer, index=False)
                    file_name = file.name.replace(file_ext, ".xlsx")
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                buffer.seek(0)

            # Download button
            if file_name and mime_type:
                st.download_button(
                    label=f"Download {file.name} as {conversion_type}",
                    data=buffer,
                    file_name=file_name,
                    mime=mime_type
                )

    st.success("All Files Processed!")
