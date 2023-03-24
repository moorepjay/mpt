from dash import Dash, html, dcc
import dash
import pandas as pd

from database import get_database

app = Dash(__name__, use_pages=True)

server = app.server

app.layout = html.Div([
    html.H1('Multi-page app with Dash Pages (updated from remote)'),

    html.Div(
        [
            html.Div(
                dcc.Link(
                    f"{page['name']} - {page['path']}", href=page["relative_path"]
                )
            )
            for page in dash.page_registry.values()
        ]
    ),

    dash.page_container
])

if __name__ == '__main__':
    app.run_server(debug=True)
