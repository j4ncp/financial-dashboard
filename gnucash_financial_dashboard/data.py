import sqlite3
import datetime
import os

import pandas as pd
import numpy as np

# --------------------------------------------------------------------------------------------
# DATA QUERY FUNCTIONS


def retrieve_accounts(gnucash_file, build_fullname=False) -> pd.DataFrame:
    # get all account data from the sqlite3 db
    conn = sqlite3.connect(gnucash_file)
    df = pd.read_sql_query("SELECT * FROM accounts", conn)
    # rename "name" to "account_name", as the former might cause problems
    # with the pd.Series.name attribute...
    df.rename(columns={"name": "account_name"}, inplace=True)
    if build_fullname:
        # create full names for each account
        # for each account, trace the route to the root account and add all intermediate accounts
        full_names = []
        for _, row in df.iterrows():
            # if this is already a root, do nothing
            if row.account_type == "ROOT":
                full_names.append("")
                continue
            # trace path up to root
            full_account_name = row["account_name"]
            cur_parent_row = df[df.guid == row["parent_guid"]].iloc[0]
            while cur_parent_row["account_type"] != "ROOT":
                # prepend parent name
                full_account_name = cur_parent_row["account_name"] + "/" + full_account_name
                # go up to parent
                cur_parent_row = df[df.guid == cur_parent_row["parent_guid"]].iloc[0]
            # append name
            full_names.append(full_account_name)
        # add unique names to df
        df["full_name"] = full_names
    return df


def retrieve_income_expense_transactions(gnucash_filename) -> pd.DataFrame:
    conn = sqlite3.connect(gnucash_filename)
    query = """
        SELECT
          transactions.post_date AS tx_date,
          splits.quantity_num AS quantity_num,
          splits.quantity_denom AS quantity_denom,
          accounts.name as account_name,
          accounts.account_type as account_type,
          accounts.guid as account_guid,
          parent_acc.guid as parent_guid,
          transactions.description as desc
        FROM transactions
        INNER JOIN splits 
          ON splits.tx_guid=transactions.guid
        INNER JOIN accounts 
          ON splits.account_guid=accounts.guid
        LEFT JOIN accounts AS parent_acc
          ON accounts.parent_guid=parent_acc.guid
        WHERE 
          accounts.account_type IN ('INCOME', 'EXPENSE')
    """
    df = pd.read_sql_query(query, conn)
    # now fix us a small issues with the dating and amounts:
    df.tx_date = pd.to_datetime(df.tx_date)
    df["ym"] = df.tx_date.dt.to_period("M")
    df["amount"] = df.quantity_num / df.quantity_denom
    del df["quantity_num"]
    del df["quantity_denom"]
    # amount in income transactions is always negative. Flip those.
    df.amount = np.where(df.account_type == "INCOME", -df.amount, df.amount)
    return df


def retrieve_account_transactions(gnucash_filename, account_guid):
    conn = sqlite3.connect(gnucash_filename)
    query = """
        SELECT
          transactions.post_date AS tx_date,
          splits.quantity_num AS quantity_num,
          splits.quantity_denom AS quantity_denom,
          accounts.name as account_name,
          accounts.account_type as account_type,
          accounts.guid as account_guid,
          transactions.description as desc
        FROM transactions
        INNER JOIN splits 
          ON splits.tx_guid=transactions.guid
        INNER JOIN accounts 
          ON splits.account_guid=accounts.guid
        WHERE 
          accounts.guid='{}'
        """.format(account_guid)
    df = pd.read_sql_query(query, conn)
    # now fix us a small issues with the dating and amounts:
    df.tx_date = pd.to_datetime(df.tx_date)
    df["amount"] = df.quantity_num / df.quantity_denom
    del df["quantity_num"]
    del df["quantity_denom"]
    # sort by date
    df.sort_values(by="tx_date", ascending=True, inplace=True, ignore_index=True)
    # compute balances
    df["balance"] = df.amount.cumsum()
    return df


def retrieve_last_updated(filename) -> str:
    timestamp = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
    return timestamp.isoformat(sep=" ", timespec="minutes")


# --------------------------------------------------------------------------------------------
# FILTERING FUNCTIONS


def filter_by_timeframe(df, from_date, to_date):
    return df[(df.tx_date >= pd.to_datetime(from_date)) &
              (df.tx_date <= pd.to_datetime(to_date))]
