
from argparse import ArgumentParser
from datetime import timedelta, datetime

from dash import Dash, html, dcc, Output, Input
import dash_bootstrap_components as dbc

from . import data
from . import plotting


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
config = {}


# --------------------------------------------------------------------------------------------
# HELPER FUNCTIONS


def format_accounts_for_dropdown(accounts_df):
    """
    Take accounts dataframe as returned by data.retrieve_accounts and bring it into
    a form that can be assigned to a dcc.Dropdown.
    """
    # Strategy:
    # use the full account name as label and the account's guid as value.
    # -> extract only the columns we need first, then rename those,
    #    then transform into records.

    # filter out placeholders and root accounts (which for some reason are not placeholders ??)
    tmp = accounts_df[(accounts_df.placeholder==0) & (accounts_df.account_type!="ROOT")]
    tmp = tmp[["full_name", "guid"]].rename(columns={"full_name": "label", "guid": "value"})
    return tmp.to_dict("records")


# --------------------------------------------------------------------------------------------
# LAYOUT - HEADER & SIDEBAR


def build_header():
    # get a few limiting data points from the DB
    tx_df = data.retrieve_income_expense_transactions(config["db"])
    max_date_ts = tx_df.tx_date.max().isoformat(sep=" ", timespec="minutes")
    # build header layout
    return html.Div([
        html.H1("Financial Dashboard"),
        html.P(config["db"], className="mono"),
        html.P("last updated: {}, last entry: {}".format(
            data.retrieve_last_updated(config["db"]),
            max_date_ts
        )),
    ], id="header")


def build_sidebar():
    # get a few limiting data points from the DB
    tx_df = data.retrieve_income_expense_transactions(config["db"])
    min_date, max_date = tx_df.tx_date.min(), tx_df.tx_date.max()
    accounts_df = data.retrieve_accounts(config["db"], build_fullname=True)
    dropdown_options = format_accounts_for_dropdown(accounts_df)
    # build layout for sidebar
    return dbc.Container([
        # Settings section
        html.Div([
            html.H2("Settings"),
            html.P("Select the date range to plot & compute aggregates from:"),
            dcc.DatePickerRange(
                id="date-range",
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=max(max_date-timedelta(days=365), min_date),  # 12 months back
                end_date=max_date
            ),
            html.P("Select the account to plot balances from:"),
            dcc.Dropdown(
                options=dropdown_options,
                value=dropdown_options[0]["value"],  # just pre-select the first one
                clearable=False,
                id="account-chooser"
            )
        ], id="fd-settings"),
        html.Div([
            # Numbers section
            html.H2("Statistics"),
            html.P("Monthly average balance in selected timeframe:"),
            html.Table([
                html.Tbody([
                    html.Tr([
                        html.Td("Income"), html.Td(id="avg-monthly-income")
                    ]),
                    html.Tr([
                        html.Td("Expense"), html.Td(id="avg-monthly-expense")
                    ]),
                    html.Tr([
                        html.Td("Balance"), html.Td(id="avg-monthly-balance")
                    ])
                ])
            ], className="fd-table"),
            html.P("Opening and closing balance for selected account:"),
            html.Table([
                html.Tbody([
                    html.Tr([
                        html.Td(id="opening-date"), html.Td(id="opening-balance")
                    ]),
                    html.Tr([
                        html.Td(id="closing-date"), html.Td(id="closing-balance")
                    ])
                ])
            ], className="fd-table")
        ], id="fd-statistics")
    ])


# --------------------------------------------------------------------------------------------
# LAYOUT - BODY
"""

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

"""


def build_content_area():
    return [dbc.Row([
        dbc.Col([
            html.H3("Monthly Income and Expenses"),
            dcc.Graph(id="monthly-balance-plot")
        ], width=12)
    ]), dbc.Row([
        dbc.Col([
            html.H3("Balance for account"),
            dcc.Graph(id="account-plot")
        ], width=12)
    ])]
    """, dbc.Row([
        dbc.Col(income_sunburst(), width=6),
        dbc.Col(expense_sunburst(), width=6)
    ])]"""


def build_layout():
    return html.Div([
        dbc.Row(build_header()),
        dbc.Row([
                dbc.Col(build_sidebar(), id="sidebar", width=4),
                dbc.Col(build_content_area(), width=8)
        ], id="below-header")
    ])

# --------------------------------------------------------------------------------------------
# CALLBACKS


# CALLBACK for monthly balance plot
@app.callback(
    Output("monthly-balance-plot", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_monthly_balance_plot(start_date, end_date):
    df = data.retrieve_income_expense_transactions(config["db"])
    df = data.filter_by_timeframe(df, start_date, end_date)
    return plotting.plot_income_expense_by_month(df)


# CALLBACK for monthly average balance table
@app.callback(
    Output("avg-monthly-income", "children"),
    Output("avg-monthly-expense", "children"),
    Output("avg-monthly-balance", "children"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_monthly_averages(start_date, end_date):
    df = data.retrieve_income_expense_transactions(config["db"])
    df = data.filter_by_timeframe(df, start_date, end_date)

    # filter for income and expenses, sum transaction values by month
    balance_ym = df.groupby(["ym", "account_type"]).sum().unstack().reset_index()

    # compute averages per month
    averages = balance_ym.amount.mean().reset_index().rename(columns={0: "avg_amount"})

    # extract from dataframe
    avg_income = averages[averages.account_type == "INCOME"].avg_amount.iloc[0]
    avg_expense = averages[averages.account_type == "EXPENSE"].avg_amount.iloc[0]

    # return formatted
    return f"{avg_income:.2f}€", \
           f"{-avg_expense:.2f}€", \
           f"{avg_income-avg_expense:.2f}€"


# CALLBACK for opening/closing table dates
@app.callback(
    Output("opening-date", "children"),
    Output("closing-date", "children"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_dates_in_account_table(start_date, end_date):
    start = datetime.fromisoformat(start_date)
    stop  = datetime.fromisoformat(end_date)
    return start.strftime("%Y %b %d"), stop.strftime("%Y %b %d")


# CALLBACK for opening/closing table balances and account plot
@app.callback(
    Output("opening-balance", "children"),
    Output("closing-balance", "children"),
    Output("account-plot", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("account-chooser", "value")
)
def update_values_in_account_table(start_date, end_date, account_guid):
    df = data.retrieve_account_transactions(config["db"], account_guid)
    # compute balances
    df.sort_values(by="tx_date", ascending=True, inplace=True, ignore_index=True)
    df["balance"] = df.amount.cumsum()
    # filter by timeframe
    df = data.filter_by_timeframe(df, start_date, end_date)
    # extract and format opening and closing balances, and add plot
    opening_amount = df.balance.iloc[0]
    closing_amount = df.balance.iloc[-1]
    return f"{opening_amount:.2f}€", \
           f"{closing_amount:.2f}€", \
           plotting.plot_account_timeline(df)


# --------------------------------------------------------------------------------------------
# SERVER


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
