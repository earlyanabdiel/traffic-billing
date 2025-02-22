import streamlit as st
import pandas as pd
from io import BytesIO

# Title of the Dashboard
st.title("Auto Billing Processing")
st.subheader("created by MBB Managed Service", divider="gray")

# File Upload
uploaded_files = st.file_uploader("Upload Excel files", type=["xlsx", "xls"], accept_multiple_files=True)

# Initialize DataFrames
df_ggsn = None
df_ix = None

# Process uploaded files
# Process uploaded files
if uploaded_files:
    for uploaded_file in uploaded_files:
        if 'GGSN' in uploaded_file.name:
            df_ggsn = pd.read_excel(uploaded_file)
        elif 'IX' in uploaded_file.name:
            df_ix = pd.read_excel(uploaded_file)

# Toggle for GGSN or IX
data_type = st.radio("Select Data Type:", ('GGSN', 'IX'))

if data_type == 'GGSN' and df_ggsn is not None:
    # Create 'link' column for GGSN
    df_ggsn['link'] = df_ggsn['metro'] + df_ggsn['port']
    df = df_ggsn
elif data_type == 'IX' and df_ix is not None:
    # Create 'link' column for IX
    df_ix['link'] = df_ix['pe_transit'] + df_ix['port']
    df = df_ix
else:
    st.warning("Please upload the correct files.")
    st.stop()

# Create 'max_max' column
df['max_max'] = df[['max_in', 'max_out']].max(axis=1)

# Convert util_time to datetime
df['util_time'] = pd.to_datetime(df['util_time'])

# Unique links for selection
unique_links = df['link'].unique()
selected_links = st.multiselect("Select Links:", unique_links)

# Create a dictionary to hold date ranges for each selected link
date_ranges = {}
for link in selected_links:
    start_date = df[df['link'] == link]['util_time'].min()
    end_date = df[df['link'] == link]['util_time'].max()
    date_ranges[link] = st.date_input(f"Select date range for {link}", [start_date, end_date])

# Calculate 95th percentile for each selected link based on the specified date range
percentile_results = []
for link, (start_date, end_date) in date_ranges.items():
    filtered_df = df[(df['link'] == link) & (df['util_time'] >= pd.Timestamp(start_date)) & (df['util_time'] <= pd.Timestamp(end_date))]
    if not filtered_df.empty:
        p95 = filtered_df['max_max'].quantile(0.95)
        percentile_results.append({'link': link, 'percentile_95': p95})

# Calculate 95th percentile for unselected links using the entire data range
unselected_links = set(unique_links) - set(selected_links)
for link in unselected_links:
    filtered_df = df[df['link'] == link]
    if not filtered_df.empty:
        p95 = filtered_df['max_max'].quantile(0.95)
        percentile_results.append({'link': link, 'percentile_95': p95})

# Display the results
if percentile_results:
    results_df = pd.DataFrame(percentile_results)
    st.subheader("95th Percentile Results")
    st.dataframe(results_df)

# Provide functionality to rename and download the processed Excel file
output_filename = st.text_input("Enter output file name (without extension | e.g Traffic_(GGSN / IX)_(MONTH)_25):", "Traffic_xxx_xxx_25")
if st.button("Download"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='dataset')
        results_df.to_excel(writer, index=False, sheet_name='summary')
    output.seek(0)
    
    st.download_button(
        label="Download Processed Excel File",
        data=output,
        file_name=f"{output_filename}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
