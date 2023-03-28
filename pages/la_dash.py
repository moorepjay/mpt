import pandas as pd
from dash import Dash, html, dcc
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots

import dash

import constant
from database import get_collection

dash.register_page(__name__)

# Connect to mongodb.
collection = get_collection('lost_ark')

# Create price data df from mongo collection.
sell_records = collection.find()
price_df = pd.DataFrame(sell_records)

# Ensure date column is properly typed.
price_df['Date'] = pd.to_datetime(price_df['Date'])

# Parse numerical price value and convert to float
price_df['Price'] = price_df['Price'].astype(float)

# Ensure 'USD' column is calculated.
# 1 chinese yuan equals 0.1433 USD https://www.currency.me.uk/convert/cny/usd
price_df['USD'] = price_df['Price'] * 0.1434

# Calculate global mean/min data.
# lost_ark_global_info = pd.read_csv(constants.LA_GLOBAL_INFO)
global_means = price_df.groupby(pd.Grouper(key='Date', axis=0, freq='D'))['USD'].mean()
global_means = global_means.rename('mean')
global_mins = price_df.groupby(pd.Grouper(key='Date', axis=0, freq='D'))['USD'].min()
global_mins = global_mins.rename('min')
global_info = pd.concat([global_means, global_mins], axis=1).reset_index()

# Calculate server mean/min data.
# lost_ark_server_info = pd.read_csv(constants.LA_SERVER_INFO)
server_means = price_df.groupby(['Server', 'Date'])['USD'].mean().reset_index().rename(columns={'USD': 'mean'})
server_mins = price_df.groupby(['Server', 'Date'])['USD'].min().reset_index().rename(columns={'USD': 'min'})
server_info = pd.concat([server_means, server_mins], axis=1)
server_info = server_info.loc[:, ~server_info.columns.duplicated()]

# Calculate region mean/min data.
# lost_ark_region_info = pd.read_csv(constants.LA_REGION_INFO)
region_means = price_df.groupby(['Region', 'Date'])['USD'].mean().reset_index().rename(columns={'USD': 'mean'})
region_mins = price_df.groupby(['Region', 'Date'])['USD'].min().reset_index().rename(columns={'USD':'min'})
region_info = pd.concat([region_means, region_mins], axis=1)
region_info = region_info.loc[:,~region_info.columns.duplicated()]

# Calculate seller information.
# lost_ark_historical_names = pd.read_csv(constants.LA_HISTORICAL_NAMES)
# lost_ark_current_names = pd.read_csv(constants.LA_CURRENT_NAMES)
names_df = price_df.groupby(['Date', 'Seller'])['USD'].count().reset_index().sort_values(by=['USD', 'Seller', 'Date'],
                                                                                         ascending=False)
historical_names_df = names_df.sort_values(by=['Date'], ascending=True)
current_names = historical_names_df.sort_values(by=['Date'], ascending=False)
current_names = current_names.drop_duplicates(subset=['Seller'], keep='first').sort_values(by=['USD'],ascending=False)
current_names = current_names.reset_index().drop('index', axis=1).rename(columns={'Seller': 'Seller','USD': 'Listings'})

la_helper_df = price_df
lost_ark_seller = la_helper_df.groupby(['Seller', 'Date'])['USD'].mean().reset_index()

# Dashboard code that includes both our "figures" (data visualizations) and the html structure of the page
fig = go.Figure()
fig.add_trace(go.Scatter(x=global_info.Date, y=global_info['min'], fill='tozeroy', name='Minimum Price (USD)',
                         legendrank=1,
                         marker_color='rgba(152, 0, 0, .8)'))
fig.add_trace(go.Scatter(x=global_info.Date, y=global_info['mean'], fill='tonexty', name='Average Price (USD)',
                         legendrank=2,
                         marker_color='rgba(212, 90, 93, .9)'))

fig.update_layout(
    title='Average Daily Sell Order Prices',
    title_font={"size": 25}
)
fig.update_xaxes(
    tickangle=30,
    title_text="Date",
    title_font={"size": 20},
    # Sets x-axis interval to one day
    dtick=86400000.0,
)
fig.update_yaxes(
    title_text="Price (USD)",
    title_standoff=25,
    title_font={"size": 20},
    exponentformat='none'
)

# figure for the daily gold sellers with most listings
fig2 = px.bar(
    data_frame=current_names.head(40),
    x='Seller',
    y='Listings',
    template='presentation',
    color='Listings',
    text_auto=True,
    title='Top Daily Listings by Seller',
    color_continuous_scale='tealgrn'
)
fig2.update_layout(
    xaxis=dict(tickfont=dict(size=10))
)

layout = html.Div(children=[
    html.H1(children='bijiaqi.com'),

    html.Div(children='''
        Historical gold prices: Lost Ark (Americas and Europe)
    '''),

    dcc.Graph(
        id='master_sell_order_data',
        figure=fig
    ),

    # server gold prices mean and min
    html.Div([
        dcc.Graph(id='lost_ark_server_and_region_prices'),
        'Select a server to view gold prices: ',
        dcc.Dropdown(
            id='lost_ark_select_server',
            options=constant.LOST_ARK_SERVER_DROPDOWN_OPTIONS,
            multi=False,
            value='Adrinne',
            style={'width': '40%'}
        ),

        'Select a region to view gold prices:',
        dcc.Dropdown(
            id='lost_ark_select_region',
            options=[
                {'label': 'EU Central', 'value': 'EU_Central'},
                {'label': 'EU West', 'value': 'EU_West'},
                {'label': 'US East', 'value': 'US_East'},
                {'label': 'US West', 'value': 'US_West'},
                {'label': 'South America', 'value': 'South_America'}
            ],
            multi=False,
            value='US_West',
            style={'width': '40%'}
        )

    ]),

    # daily gold seller listings
    html.H2('Gold Sellers with the Most Listings'),
    html.Div([
        dcc.Graph(id='gold_sellers',
                  figure=fig2)
    ]),

    # Graph for individual seller information
    html.Div(
        html.Div([
            dcc.Graph(id='lost_ark_individual_seller_info'),
            'Input Seller Name (case-sensitive): ',
            dcc.Input(id='lost_ark_user_input', value='大师', type='text')
        ])
    ),
])


@dash.callback(
    Output(component_id='lost_ark_server_and_region_prices', component_property='figure'),
    Input(component_id='lost_ark_select_server', component_property='value'),
    Input(component_id='lost_ark_select_region', component_property='value')
)
def update_server_region_graph(selected_server, selected_region):
    server_df = server_info.copy()
    server_df = server_df[server_df['Server'] == selected_server]

    region_df = region_info.copy()
    region_df = region_df[region_df['Region'] == selected_region]

    fig1 = make_subplots(rows=1, cols=2,
                         subplot_titles=[f'Prices in {selected_server}', f'Prices in {selected_region}'])
    fig1.add_trace(
        go.Scatter(x=server_df['Date'], y=server_df['min'], fill='tozeroy', name='Server Min Price', legendrank=4),
        row=1, col=1
    )
    fig1.add_trace(
        go.Scatter(x=server_df['Date'], y=server_df['mean'], fill='tonexty', name='Server Average Price', legendrank=3),
        row=1, col=1
    )

    fig1.add_trace(
        go.Scatter(x=region_df['Date'], y=region_df['min'], fill='tozeroy', name='Region Min Price', legendrank=2),
        row=1, col=2
    )
    fig1.add_trace(
        go.Scatter(x=region_df['Date'], y=region_df['mean'], fill='tonexty', name='Region Average Price', legendrank=1),
        row=1, col=2
    )

    fig1.update_xaxes(title_text='Date')
    # fig1.update_xaxes(title_text='Date', row=1, col=2)
    fig1.update_yaxes(title_text='Price', exponentformat='none')

    return fig1


@dash.callback(
    Output(component_id='lost_ark_individual_seller_info', component_property='figure'),
    Input(component_id='lost_ark_user_input', component_property='value')
)
def update_seller_info(seller_name):
    temp = current_names.copy()

    filtered_df6 = lost_ark_seller[lost_ark_seller['Seller'] == seller_name]
    filtered_df = temp[temp['Seller'] == seller_name]
    fig1 = make_subplots(rows=1, cols=2,
                         subplot_titles=('Number of Listings', 'Average Price'))
    fig1.add_trace(
        go.Scatter(x=filtered_df['Date'], y=filtered_df['Listings'], name='Number of Listings'),
        row=1, col=1)
    fig1.add_trace(
        go.Scatter(x=filtered_df6['Date'], y=filtered_df6['USD'], name='Average Price'),
        row=1, col=2)

    # updating x-axis labels
    fig1.update_xaxes(title_text='Date', row=1, col=1)
    fig1.update_xaxes(title_text='Date', row=1, col=2)

    # updating y-axis labels
    fig1.update_yaxes(title_text='Listings', row=1, col=1)
    fig1.update_yaxes(title_text='Average Price', row=1, col=2)
    return fig1