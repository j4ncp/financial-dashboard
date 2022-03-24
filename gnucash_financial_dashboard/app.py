
from argparse import ArgumentParser
from datetime import timedelta

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from .data import retrieve_tx_date_range, \
                  retrieve_last_updated, \
                  retrieve_last_tx_date, \
                  retrieve_income_expense_balances

from .plotting import plot_income_expense_by_month, plot_accounts_sunburst


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
config = {}


def build_header():
    return html.Div([
        html.H1("Financial Dashboard"),
        html.P(config["db"], className="mono"),
        html.P("last updated: {}, last entry: {}".format(
            retrieve_last_updated(config["db"]),
            retrieve_last_tx_date(config["db"])
        )),
    ], id="header")


def build_sidebar():
    min_date, max_date = retrieve_tx_date_range(config["db"])
    return dbc.Container([
        html.H2("Settings"),
        html.P("Select the date range to plot & compute aggregates from:"),
        dcc.DatePickerRange(
            id="date-range",
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            start_date=max(max_date-timedelta(days=365), min_date),  # 12 months back
            end_date=max_date
        )
    ])


def balance_graph():
    return dcc.Graph(
        id="balances-plot",
        figure=plot_income_expense_by_month(config["db"], "2020-01-01", "2020-12-31")
    )


def balance_totals_area():
    avg_income, avg_expense = retrieve_income_expense_balances(config["db"], "2020-01-01", "2020-12-31")
    return dbc.Container([
        html.H3("Monthly Average"),
        html.P("in selected timeframe"),
        html.Table([
            html.Tbody([
                html.Tr([
                    html.Td("Income"), html.Td(f"{avg_income:.2f}€")
                ]),
                html.Tr([
                    html.Td("Expense"), html.Td(f"{-avg_expense:.2f}€")
                ]),
                html.Tr([
                    html.Td("Balance"), html.Td(f"{avg_income-avg_expense:.2f}€")
                ])
            ])
        ], id="monthly-avg-table")
    ])


def build_content_area():
    return dbc.Row([
        dbc.Col(balance_graph(), width=9),
        dbc.Col(balance_totals_area(), width=3, className="align-self-center")
    ])


def build_layout():
    return html.Div([
        dbc.Row(build_header()),
        dbc.Row([
                dbc.Col(build_sidebar(), id="sidebar", width=3),
                dbc.Col(build_content_area(), width=9)
        ], id="below-header")
    ])


def run_server(gnucash_file):
    global config
    config["db"] = gnucash_file
    app.layout = build_layout()
    app.run_server(debug=True)


def main():
    parser = ArgumentParser(description="A small dashboard server to display interactive stats about a GnuCash ledger file in sqlite3 format.")
    parser.add_argument("GNUCASH_FILE", help="A GnuCash ledger file in sqlite3 format")
    args = parser.parse_args()
    run_server(args.GNUCASH_FILE)


if __name__ == "__main__":
    main()
