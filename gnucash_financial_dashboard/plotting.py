

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

"""
def plot_accounts_sunburst(filename, from_date, to_date, account_type="EXPENSE"):
    data = retrieve_income_expense_transactions(filename)
    # filter down dataframe by the timeframe and account type
    frame = data[(data.tx_date >= pd.to_datetime(from_date)) &
                 (data.tx_date <= pd.to_datetime(to_date)) &
                 (data.account_type == account_type)]

    # sum all transaction values for each account
    account_data = retrieve_accounts(filename)
    account_data = account_data[account_data.account_type == account_type]
    account_data.rename(columns={"guid": "account_guid"}, inplace=True)
    account_balances = account_data.join(frame.groupby("account_guid").sum(), on="account_guid")

    # we need to massage the data a bit:
    # - the root node must be denoted by an empty string. Find the root
    #   account by choosing the account with a parent, whose parent id never occurs as account_guid.
    root_guid = account_balances[~account_balances.parent_guid.isin(account_balances.account_guid)].account_guid.iloc[0]
    account_balances.loc[account_balances.account_guid == root_guid, "parent_guid"] = ""

    # - compute aggregates for all accounts recursively
    def aggregate_balance_for_guid(guid):
        if pd.isna(account_balances[account_balances.account_guid == guid].amount.iloc[0]):
            # aggregate the amounts of all subordinate accounts
            # -> fetch subordinate accounts
            subordinates = account_balances[account_balances.parent_guid == guid]
            for _, sub_acc in subordinates.iterrows():
                aggregate_balance_for_guid(sub_acc.account_guid)
            # now every subordinate should have a valid amount
            amount_sum = account_balances[account_balances.parent_guid == guid].amount.sum()
            account_balances.loc[account_balances.account_guid == guid, "amount"] = amount_sum

    # call it on the root node, then all entries should be valid
    aggregate_balance_for_guid(root_guid)
    assert not account_balances.amount.isna().any()

    # plot
    fig = go.Figure()
    fig.add_trace(
        go.Sunburst(
            name=account_type,
            ids=account_balances.account_guid,
            labels=account_balances.account_name,
            parents=account_balances.parent_guid,
            values=account_balances.amount,
            branchvalues="total",
            hovertemplate="<br>".join([
                "Account: %{label}",
                "Amount: %{value:.2f}€",
                "Fraction: %{percentRoot:.1%}"
            ])
        )
    )
    fig.update_layout(
        height=700,
        colorway=px.colors.qualitative.Set3
    )

    return fig
"""

def plot_income_expense_by_month(df):
    """
    Make a bar plot for income and expenses by month in the given timeframe.
    Given dataframe needs to be filtered to desired timeframe
    """
    # filter for income and expenses
    income = df[df.account_type == "INCOME"]
    expense = df[df.account_type == "EXPENSE"]
    balance_ym = df.groupby(["ym", "account_type"]).sum().unstack().reset_index()

    # make plot
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Income",
            x=income.ym.astype("str"),
            y=income.amount,
            marker_color="green",
            customdata=income[["account_name", "desc"]],
            hovertemplate='<br>'.join([
                "Account: %{customdata[0]}",
                "Desc: %{customdata[1]}",
                "Amount: %{y}€"
            ])
        )
    )
    fig.add_trace(
        go.Bar(
            name="Expenses",
            x=expense.ym.astype("str"),
            y=-expense.amount,
            marker_color="red",
            customdata=expense[["account_name", "desc"]],
            hovertemplate='<br>'.join([
                "Account: %{customdata[0]}",
                "Desc: %{customdata[1]}",
                "Amount: %{y}€"
            ])
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Balance",
            x=balance_ym["ym"].astype("str"),
            y=balance_ym.amount.INCOME - balance_ym.amount.EXPENSE,
            marker_color="yellow",
            hovertemplate='<br>'.join([
                "Balance: %{y}€",
                "Month: %{x|%B %Y}"
            ])
        )
    )
    fig.update_layout(
        #xaxis_title="",
        #yaxis_title="Amount [€]",
        template="plotly_white",
        barmode="relative",
        margin=dict(r=0, l=0, t=0, b=0),
        legend=dict(yanchor="top", y=0.99, x=0.01, xanchor="left")
    )
    return fig


def plot_account_timeline(df):
    """
    Make a line plot for the balance of a given account
    Given dataframe needs to be filtered to desired timeframe
    """
    # make plot
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            name="",  # disable name to not show "trace 0"
            x=df.tx_date,
            y=df.balance,
            marker_color="blue",
            customdata=df[["amount", "desc"]],
            hovertemplate='<br>'.join([
                "Balance: %{y}€",
                "Date: %{x}",
                "Amount: %{customdata[0]}€",
                "Desc: %{customdata[1]}"
            ])
        )
    )
    fig.update_layout(
        #xaxis_title="",
        #yaxis_title="Balance [€]"
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig
