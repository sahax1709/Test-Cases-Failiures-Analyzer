import pandas as pd

def group_failures(failure_data):
    # Convert dates to datetime for proper sorting
    failure_data = failure_data.copy()
    failure_data['Date_dt'] = pd.to_datetime(
        failure_data['Date'],
        format='%d %B %Y',
        errors='coerce'
    )
    
    # Group and aggregate with proper date sorting
    grouped = failure_data.groupby('Scenario').agg({
        'Date': 'count',
        'Date_dt': ['min', 'max']
    })
    
    # Flatten multi-index columns
    grouped.columns = ['Failures', 'First Failed_dt', 'Last Failed_dt']
    
    # Convert datetime back to original string format
    grouped['First Failed'] = grouped['First Failed_dt'].dt.strftime('%d %B %Y')
    grouped['Last Failed'] = grouped['Last Failed_dt'].dt.strftime('%d %B %Y')
    
    # Select and sort final columns
    grouped = grouped[['Failures', 'First Failed', 'Last Failed']]
    grouped = grouped.sort_values('Failures', ascending=False)
    
    return grouped
