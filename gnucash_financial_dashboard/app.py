
from argparse import ArgumentParser
from datetime import timedelta

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

import pandas as pd

from .data import retrieve_tx_date_range, \
                  retrieve_last_updated, \
                  retrieve_last_tx_date, \
                  retrieve_income_expense_balances, \
                  retrieve_account_balances

from .plotting import plot_income_expense_by_month, plot_accounts_sunburst, plot_account_balances


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
    return [
        html.H3("Monthly Income and Expenses"),
        dcc.Graph(
            id="balances-plot",
            figure=plot_income_expense_by_month(config["db"], "2020-01-01", "2020-12-31")
        )
    ]


def balance_account_graph():
    return [
        html.H3("Balance for account Girokonto"),
        dcc.Graph(
            id="account-plot",
            figure=plot_account_balances(config["db"], "Girokonto", "2020-01-01", "2020-12-31")
        )
    ]


def income_sunburst():
    return [
        html.H3(f"Income distribution"),
        dcc.Graph(
            id="income-sunburst",
            figure=plot_accounts_sunburst(config["db"], "2020-01-01", "2020-12-31", account_type="INCOME")
        )
    ]


def expense_sunburst():
    return [
        html.H3(f"Income distribution"),
        dcc.Graph(
            id="expense-sunburst",
            figure=plot_accounts_sunburst(config["db"], "2020-01-01", "2020-12-31", account_type="EXPENSE")
        )
    ]


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
        ], id="monthly-avg-table", className="fd-table")
    ])


def balance_account_stat_area():
    account_name = "Girokonto"
    from_date, to_date = "2020-01-01", "2020-12-31"
    # compute first and last balance
    tx = retrieve_account_balances(config["db"], account_name)
    data_frame = tx[(tx.tx_date >= pd.to_datetime(from_date)) &
                    (tx.tx_date <= pd.to_datetime(to_date))]
    from_balance = data_frame.balance.iloc[0]
    to_balance = data_frame.balance.iloc[-1]

    return dbc.Container([
        html.H3(account_name),
        html.Table([
            html.Tbody([
                html.Tr([
                    html.Td(f"{from_date}"), html.Td(f"{from_balance:.2f}€")
                ]),
                html.Tr([
                    html.Td(f"{to_date}"), html.Td(f"{to_balance:.2f}€")
                ])
            ])
        ], id="account-balance-table", className="fd-table")
    ])


def build_content_area():
    return [dbc.Row([
        dbc.Col(balance_graph(), width=9),
        dbc.Col(balance_totals_area(), width=3, className="align-self-center")
    ]), dbc.Row([
        dbc.Col(balance_account_graph(), width=9),
        dbc.Col(balance_account_stat_area(), width=3, className="align-self-center")
    ]), dbc.Row([
        dbc.Col(income_sunburst(), width=6),
        dbc.Col(expense_sunburst(), width=6)
    ])]


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
