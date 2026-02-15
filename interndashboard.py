import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, time
import pytz
import numpy as np
import os
import webbrowser

# ==========================================
# 1. CONFIGURATION
# ==========================================

IGNORE_TIME_LIMITS = False  # ⬅️ Set True to show all charts (testing)

try:
    df = pd.read_csv('play store data.csv')
except FileNotFoundError:
    print("❌ play store data.csv not found")
    exit()

ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)
current_time = now.time()

print("Current IST Time:", current_time)

# ==========================================
# 2. DATA CLEANING
# ==========================================

df['Installs'] = df['Installs'].astype(str).str.replace(r'[+,]', '', regex=True)
df['Installs'] = pd.to_numeric(df['Installs'], errors='coerce')

df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce')
df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')

df['Price'] = df['Price'].astype(str).str.replace('$', '', regex=False).replace(['Free','free'],'0')
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

def clean_size(x):
    x = str(x)
    if 'M' in x:
        return float(x.replace('M',''))
    if 'k' in x:
        return float(x.replace('k','')) / 1024
    return np.nan

df['Size_MB'] = df['Size'].apply(clean_size)

df['Last Updated'] = pd.to_datetime(df['Last Updated'], errors='coerce')
df['Month'] = df['Last Updated'].dt.to_period('M').dt.to_timestamp()
df['Category'] = df['Category'].str.upper()

# ==========================================
# 3. CHART FUNCTIONS
# ==========================================

def chart1():
    temp = df[(df['Rating']>=4) & (df['Size_MB']>=10)]
    if temp.empty: return None
    grp = temp.groupby('Category').agg(Rating=('Rating','mean'),
                                       Reviews=('Reviews','sum')).reset_index()
    top = grp.sort_values('Reviews', ascending=False).head(10)
    m = top.melt(id_vars='Category')
    return px.bar(m, x='Category', y='value', color='variable',
                  barmode='group', title='Ratings vs Reviews')

def chart2():
    temp = df[df['Installs']>10000]
    if temp.empty: return None
    top = temp.groupby('Category')['Installs'].sum().nlargest(3).index
    agg = temp[temp['Category'].isin(top)].groupby(['Category','Type']).agg(
        Installs=('Installs','mean'),
        Price=('Price','mean')).reset_index()
    fig = go.Figure()
    for t in ['Free','Paid']:
        s = agg[agg['Type']==t]
        fig.add_bar(x=s['Category'], y=s['Installs'], name=f'{t} Installs')
        fig.add_scatter(x=s['Category'], y=s['Price'], yaxis='y2',
                        mode='lines+markers', name=f'{t} Price')
    fig.update_layout(title='Installs vs Price',
                      yaxis=dict(title='Installs'),
                      yaxis2=dict(title='Price', overlaying='y', side='right'))
    return fig

def chart3():
    temp = df.copy()
    temp['Country'] = 'India'
    top = temp.groupby('Category')['Installs'].sum().nlargest(5).index
    temp = temp[temp['Category'].isin(top)]
    if temp.empty: return None
    return px.choropleth(temp, locations='Country',
                         locationmode='country names',
                         color='Installs',
                         animation_frame='Category',
                         title='Installs by Category (India)')

def chart4():
    temp = df[(df['Rating']>=4.2) & (df['Reviews']>1000)]
    grp = temp.groupby(['Month','Category'])['Installs'].sum().reset_index()
    if grp.empty: return None
    return px.area(grp, x='Month', y='Installs', color='Category',
                   title='Cumulative Growth')

def chart5():
    temp = df[(df['Installs']>50000) & (df['Reviews']>500)]
    if temp.empty: return None
    return px.scatter(temp, x='Size_MB', y='Rating',
                      size='Installs', color='Category',
                      title='Size vs Rating')

def chart6():
    temp = df[df['Reviews']>500]
    grp = temp.groupby(['Month','Category'])['Installs'].sum().reset_index()
    if grp.empty: return None
    return px.line(grp, x='Month', y='Installs', color='Category',
                   title='Category Trend')

# ==========================================
# 4. TIME CONFIG
# ==========================================

charts_config = [
    ("Chart 1", chart1, time(13,0), time(14,0)),
    ("Chart 2", chart2, time(14,0), time(15,0)),
    ("Chart 3", chart3, time(15,0), time(16,0)),
    ("Chart 4", chart4, time(16,0), time(17,0)),
    ("Chart 5", chart5, time(17,0), time(18,0)),
    ("Chart 6", chart6, time(18,0), time(19,0)),
]

html = ""

for title, func, start, end in charts_config:
    allowed = (start <= current_time <= end) or IGNORE_TIME_LIMITS
    html += f"<h2>{title}</h2>"
    if allowed:
        fig = func()
        if fig:
            html += pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
        else:
            html += "<p>No data available</p>"
    else:
        html += f"""
        <div style="padding:40px;border:2px dashed red;text-align:center;">
            🔒 Available between <b>{start.strftime('%H:%M')}</b> and <b>{end.strftime('%H:%M')}</b> IST
        </div>
        """

# ==========================================
# 5. FINAL HTML
# ==========================================

final_html = f"""
<html>
<head><title>Time Based Dashboard</title></head>
<body>
<h1 style="text-align:center;">Play Store Analytics (IST)</h1>
<p style="text-align:center;">Generated at {now.strftime('%H:%M:%S')} IST</p>
{html}
</body>
</html>
"""

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(final_html)

webbrowser.open("file://" + os.path.abspath("dashboard.html"))
print("✅ Time-based dashboard opened")