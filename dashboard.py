import dash
from dash import dcc, html, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
from flask import Flask, request, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os

server = Flask(__name__)
app = dash.Dash(__name__, 
                server=server,
                external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

app.title = "Crypto AI Trading Dashboard"

server.secret_key = os.getenv('SECRET_KEY', 'super_secret_key')
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.getenv('DASH_USERNAME') and password == os.getenv('DASH_PASSWORD'):
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    '''

@server.before_request
@login_required
def require_login():
    pass

app.layout = dbc.Container([
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand(
                html.H1("Crypto AI Trading Dashboard", className="text-white"),
                className="me-auto"
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Portfolio", href="#portfolio", id="portfolio-link")),
                        dbc.NavItem(dbc.NavLink("Trades", href="#trades", id="trades-link")),
                        dbc.NavItem(dbc.NavLink("Sentiment", href="#sentiment", id="sentiment-link")),
                        dbc.NavItem(dbc.NavLink("Risk", href="#risk", id="risk-link")),
                        dbc.NavItem(dbc.NavLink("Market", href="#market", id="market-link")),
                        dbc.NavItem(dbc.NavLink("Settings", href="#settings", id="settings-link")),
                        dbc.NavItem(dbc.NavLink("3D Visualization", href="#3d-visual", id="3d-visual-link")),
                        dbc.NavItem(dbc.NavLink("MT5 Data", href="#mt5-data", id="mt5-data-link")),
                        dbc.NavItem(dbc.NavLink("Forecast", href="#forecast", id="forecast-link")),
                    ],
                    className="ms-auto",
                    navbar=True
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ]),
        color="primary",
        dark=True,
        className="mb-4"
    ),
    
    dbc.Tabs([
        dbc.Tab(label="Portfolio", tab_id="portfolio", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Current Value"),
                    dbc.CardBody(html.H5(id="current-value", children="$0.00", className="text-center"))
                ], className="mb-4"), width=2),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Drawdown"),
                    dbc.CardBody(html.H5(id="current-drawdown", children="0.00%", className="text-center"))
                ], className="mb-4"), width=2),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Peak Value"),
                    dbc.CardBody(html.H5(id="peak-value", children="$0.00", className="text-center"))
                ], className="mb-4"), width=2),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Risk %"),
                    dbc.CardBody(html.H5(id="risk-percent", children="1.0%", className="text-center"))
                ], className="mb-4"), width=2),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Sharpe Ratio"),
                    dbc.CardBody(html.H5(id="sharpe-ratio", children="0.00", className="text-center"))
                ], className="mb-4"), width=2),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Profit Factor"),
                    dbc.CardBody(html.H5(id="profit-factor", children="0.00", className="text-center"))
                ], className="mb-4"), width=2)
            ]),
            
            dbc.Card([
                dbc.CardHeader("Portfolio Value Over Time"),
                dbc.CardBody(dcc.Graph(id="portfolio-chart", style={"height": "400px"}))
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardHeader("Drawdown Analysis"),
                dbc.CardBody(dcc.Graph(id="drawdown-chart", style={"height": "400px"}))
            ])
        ]),
        
        dbc.Tab(label="Trades", tab_id="trades", children=[
            dbc.Card([
                dbc.CardHeader("Trade History"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id="trade-filter",
                        options=[
                            {'label': 'All', 'value': 'all'},
                            {'label': 'Buys', 'value': 'buy'},
                            {'label': 'Sells', 'value': 'sell'}
                        ],
                        value='all',
                        clearable=False,
                        style={"width": "200px", "marginBottom": "10px"}
                    ),
                    dash_table.DataTable(
                        id='trade-table',
                        columns=[
                            {"name": "Time", "id": "timestamp"},
                            {"name": "Action", "id": "action"},
                            {"name": "Amount", "id": "amount"},
                            {"name": "Price", "id": "price"},
                            {"name": "Cost", "id": "cost"},
                            {"name": "Symbol", "id": "symbol"}
                        ],
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_header={
                            'backgroundColor': 'rgb(30, 30, 30)',
                            'color': 'white'
                        },
                        style_data={
                            'backgroundColor': 'rgb(50, 50, 50)',
                            'color': 'white'
                        }
                    )
                ])
            ])
        ]),
        
        dbc.Tab(label="Sentiment", tab_id="sentiment", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Sentiment Analysis"),
                    dbc.CardBody(dcc.Graph(id="sentiment-chart", style={"height": "400px"}))
                ]), width=8),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Current Sentiment"),
                    dbc.CardBody([
                        dcc.Graph(id="sentiment-gauge", 
                                  figure=go.Figure(go.Indicator(
                                      mode="gauge+number",
                                      value=0,
                                      title={'text': "Sentiment"},
                                      gauge={
                                          'axis': {'range': [-1, 1]},
                                          'bar': {'color': "darkblue"},
                                          'steps': [
                                              {'range': [-1, -0.5], 'color': "red"},
                                              {'range': [-0.5, 0.5], 'color': "gray"},
                                              {'range': [0.5, 1], 'color': "green"}
                                          ]
                                      }
                                  )),
                                  style={"height": "300px"})
                    ])
                ]), width=4)
            ]),
            
            dbc.Card([
                dbc.CardHeader("Sentiment Sources"),
                dbc.CardBody(dcc.Graph(id="source-chart", style={"height": "400px"}))
            ])
        ]),
        
        dbc.Tab(label="Risk", tab_id="risk", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Drawdown Progression"),
                    dbc.CardBody(dcc.Graph(id="drawdown-progress", style={"height": "300px"}))
                ]), width=6),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Risk Management"),
                    dbc.CardBody([
                        html.H4("Current Risk: ", id="current-risk"),
                        dcc.Slider(id="risk-slider", min=0.1, max=5.0, step=0.1, value=1.0, disabled=True),
                        html.Div(id="risk-slider-value", children="1.0%")
                    ])
                ]), width=6)
            ]),
            
            dbc.Card([
                dbc.CardHeader("Risk-Adjusted Returns"),
                dbc.CardBody(dcc.Graph(id="sharpe-chart", style={"height": "400px"}))
            ])
        ]),
        
        dbc.Tab(label="Market", tab_id="market", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Market Conditions"),
                    dbc.CardBody([
                        html.H4("Current Regime: ", id="market-regime"),
                        dcc.Graph(id="market-regime-gauge", 
                                  figure=go.Figure(go.Indicator(
                                      mode="gauge+number",
                                      value=0,
                                      title={'text': "Market Regime"},
                                      gauge={
                                          'axis': {'range': [0, 2]},
                                          'steps': [
                                              {'range': [0, 0.5], 'color': "red"},
                                              {'range': [0.5, 1.5], 'color': "gray"},
                                              {'range': [1.5, 2], 'color': "green"}
                                          ],
                                          'bar': {'color': "darkblue"},
                                          'threshold': {
                                              'line': {'color': "red", 'width': 4},
                                              'thickness': 0.75,
                                              'value': 1
                                          }
                                      }
                                  )),
                                  style={"height": "300px"})
                    ])
                ]), width=6),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Asset Correlation"),
                    dbc.CardBody(dcc.Graph(id="correlation-chart", style={"height": "300px"}))
                ]), width=6)
            ]),
            
            dbc.Card([
                dbc.CardHeader("Market Volatility"),
                dbc.CardBody(dcc.Graph(id="volatility-chart", style={"height": "400px"}))
            ])
        ]),
        
        dbc.Tab(label="3D Visualization", tab_id="3d-visual", children=[
            dbc.Card([
                dbc.CardHeader("3D Portfolio & Volatility Analysis"),
                dbc.CardBody([
                    dcc.Graph(id="3d-portfolio-chart", style={"height": "600px"}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Time Window (days)"),
                            dcc.Slider(id='time-window', min=7, max=180, step=7, value=30)
                        ], width=6),
                        dbc.Col([
                            html.Label("Volatility Threshold"),
                            dcc.Slider(id='vol-threshold', min=0.01, max=0.1, step=0.01, value=0.05)
                        ], width=6)
                    ])
                ])
            ])
        ]),
        
        dbc.Tab(label="MT5 Data", tab_id="mt5-data", children=[
            dbc.Card([
                dbc.CardHeader("MetaTrader 5 Data"),
                dbc.CardBody([
                    dcc.Graph(id="mt5-chart", style={"height": "500px"}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Symbol"),
                            dcc.Dropdown(
                                id="mt5-symbol",
                                options=[
                                    {'label': 'EURUSD', 'value': 'EURUSD'},
                                    {'label': 'GBPUSD', 'value': 'GBPUSD'},
                                    {'label': 'XAUUSD', 'value': 'XAUUSD'}
                                ],
                                value='EURUSD'
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Timeframe"),
                            dcc.Dropdown(
                                id="mt5-timeframe",
                                options=[
                                    {'label': '1h', 'value': 'TIMEFRAME_H1'},
                                    {'label': '4h', 'value': 'TIMEFRAME_H4'},
                                    {'label': '1d', 'value': 'TIMEFRAME_D1'}
                                ],
                                value='TIMEFRAME_H1'
                            )
                        ], width=6)
                    ])
                ])
            ])
        ]),
        
        dbc.Tab(label="Forecast", tab_id="forecast", children=[
            dbc.Card([
                dbc.CardHeader("Portfolio Forecast"),
                dbc.CardBody([
                    dcc.Graph(id="forecast-chart", style={"height": "500px"}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Forecast Period (days)"),
                            dcc.Slider(id='forecast-days', min=7, max=90, step=7, value=30)
                        ], width=6),
                        dbc.Col([
                            html.Label("Confidence Interval"),
                            dcc.Slider(id='confidence-level', min=80, max=99, step=1, value=95)
                        ], width=6)
                    ])
                ])
            ])
        ])
    ]),
    
    dcc.Store(id='portfolio-data'),
    dcc.Store(id='trade-data'),
    dcc.Store(id='sentiment-data'),
    dcc.Store(id='market-data'),
    dcc.Store(id='risk-data'),
    dcc.Store(id='mt5-data'),
    dcc.Store(id='forecast-data'),
    
    dcc.Interval(
        id='interval-component',
        interval=10*1000,
        n_intervals=0
    )
], fluid=True)

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)