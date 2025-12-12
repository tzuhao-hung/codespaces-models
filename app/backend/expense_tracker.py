"""Expense tracking utilities for personal and shared spending.

The module defines a small SQLite schema and helper methods to manage
personal income/expense records alongside shared expenses similar to
Splitwise. It focuses on correctness and readability rather than a UI layer.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Dict, Iterable, List, Optional


class ExpenseTracker:
    """Provide CRUD helpers for personal and shared expenses.

    Database schema overview
    ------------------------
    * users: registered participants.
    * personal_transactions: income or expense entries for a single user.
    * shared_expenses: a group expense with one payer and optional category.
    * shared_splits: owed share per participant; supports percentage or fixed.
    """

    CATEGORY_CHOICES = {
        "grocery",
        "clothing",
        "entertainment",
        "dining",
        "rent",
        "transportation",
        "others",
    }

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create tables if they do not yet exist."""

        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS personal_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    amount REAL NOT NULL CHECK(amount >= 0),
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    note TEXT
                );
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    total_amount REAL NOT NULL CHECK(total_amount >= 0),
                    date TEXT NOT NULL,
                    paid_by INTEGER NOT NULL REFERENCES users(id),
                    category TEXT NOT NULL
                );
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_splits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_id INTEGER NOT NULL REFERENCES shared_expenses(id),
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    split_type TEXT NOT NULL CHECK(split_type IN ('percentage', 'fixed')),
                    value REAL NOT NULL CHECK(value >= 0),
                    owed_amount REAL NOT NULL CHECK(owed_amount >= 0)
                );
                """
            )
            self.conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_shared_split_unique
                ON shared_splits(expense_id, user_id);
                """
            )

    # ------------------------
    # Basic CRUD helpers
    # ------------------------

    def add_user(self, name: str) -> int:
        """Insert a new participant and return the new user id."""

        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO users(name) VALUES (?)",
                (name.strip(),),
            )
        return cursor.lastrowid

    def add_personal_transaction(
        self,
        user_id: int,
        t_type: str,
        amount: float,
        date: str,
        category: str,
        note: str = "",
    ) -> int:
        """Add an income or expense record for a single user."""

        normalized_category = category.lower()
        if normalized_category not in self.CATEGORY_CHOICES:
            normalized_category = "others"

        if t_type not in {"income", "expense"}:
            raise ValueError("type must be 'income' or 'expense'")

        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO personal_transactions(user_id, type, amount, date, category, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, t_type, amount, date, normalized_category, note),
            )
        return cursor.lastrowid

    # ------------------------
    # Shared expense handling
    # ------------------------

    def add_shared_expense(
        self,
        title: str,
        total_amount: float,
        date: str,
        paid_by: int,
        category: str,
        splits: Iterable[Dict],
    ) -> int:
        """Create a shared expense and associated splits.

        Each ``splits`` item must contain ``user_id``, ``split_type`` ("percentage" or
        "fixed"), and ``value``. The method computes ``owed_amount`` per participant,
        validates totals, and records what each person owes.
        """

        normalized_category = category.lower()
        if normalized_category not in self.CATEGORY_CHOICES:
            normalized_category = "others"

        prepared_splits: List[Dict] = []
        for item in splits:
            user_id = int(item["user_id"])
            split_type = item["split_type"]
            value = float(item["value"])
            if split_type not in {"percentage", "fixed"}:
                raise ValueError("split_type must be 'percentage' or 'fixed'")
            prepared_splits.append({"user_id": user_id, "split_type": split_type, "value": value})

        if not prepared_splits:
            raise ValueError("At least one participant is required")

        # Calculate owed amounts
        percentage_total = sum(s["value"] for s in prepared_splits if s["split_type"] == "percentage")
        fixed_total = sum(s["value"] for s in prepared_splits if s["split_type"] == "fixed")

        if percentage_total and abs(percentage_total - 100.0) > 0.01:
            raise ValueError("Percentage splits must add up to 100%")

        owed_amounts: List[Dict[str, float]] = []
        for split in prepared_splits:
            if split["split_type"] == "percentage":
                owed_amount = total_amount * (split["value"] / 100.0)
            else:
                owed_amount = split["value"]
            owed_amounts.append({"user_id": split["user_id"], "owed_amount": round(owed_amount, 2)})

        total_owed = sum(item["owed_amount"] for item in owed_amounts)
        rounding_gap = round(total_amount - total_owed, 2)

        if abs(rounding_gap) > 0.01 and not percentage_total:
            raise ValueError("Fixed splits must add up to the total amount")

        # Ensure the payer absorbs any rounding remainder when percentages are used.
        if abs(rounding_gap) > 0 and percentage_total:
            for item in owed_amounts:
                if item["user_id"] == paid_by:
                    item["owed_amount"] = round(item["owed_amount"] + rounding_gap, 2)
                    break

        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO shared_expenses(title, total_amount, date, paid_by, category)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, total_amount, date, paid_by, normalized_category),
            )
            expense_id = cursor.lastrowid

            for split, calculated in zip(prepared_splits, owed_amounts):
                self.conn.execute(
                    """
                    INSERT INTO shared_splits(expense_id, user_id, split_type, value, owed_amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        expense_id,
                        split["user_id"],
                        split["split_type"],
                        split["value"],
                        calculated["owed_amount"],
                    ),
                )

        return expense_id

    def calculate_balances(self) -> List[Dict[str, float]]:
        """Summarize who owes whom across all shared expenses."""

        cursor = self.conn.execute(
            """
            SELECT se.paid_by AS creditor, ss.user_id AS debtor, ss.owed_amount
            FROM shared_expenses se
            JOIN shared_splits ss ON se.id = ss.expense_id
            """
        )

        owed = defaultdict(float)
        for row in cursor:
            creditor = int(row["creditor"])
            debtor = int(row["debtor"])
            amount = float(row["owed_amount"])
            if creditor == debtor:
                # The payer's own share does not create a balance.
                continue
            owed[(debtor, creditor)] += amount

        balances = []
        participants = set()
        for debtor, creditor in owed:
            participants.add((debtor, creditor))
            participants.add((creditor, debtor))

        processed_pairs = set()
        for debtor, creditor in participants:
            if (creditor, debtor) in processed_pairs or debtor == creditor:
                continue
            net = owed.get((debtor, creditor), 0) - owed.get((creditor, debtor), 0)
            if net > 0:
                balances.append({"from": debtor, "to": creditor, "amount": round(net, 2)})
            elif net < 0:
                balances.append({"from": creditor, "to": debtor, "amount": round(abs(net), 2)})
            processed_pairs.add((debtor, creditor))
            processed_pairs.add((creditor, debtor))

        return balances

    # ------------------------
    # Reporting helpers
    # ------------------------

    def monthly_personal_summary(self, user_id: int, year: int, month: int) -> Dict[str, float]:
        """Return total income, expenses, and savings for one user in a month."""

        pattern = f"{year:04d}-{month:02d}-%"
        income = self._scalar(
            """
            SELECT COALESCE(SUM(amount), 0) FROM personal_transactions
            WHERE user_id = ? AND type = 'income' AND date LIKE ?
            """,
            (user_id, pattern),
        )
        expenses = self._scalar(
            """
            SELECT COALESCE(SUM(amount), 0) FROM personal_transactions
            WHERE user_id = ? AND type = 'expense' AND date LIKE ?
            """,
            (user_id, pattern),
        )
        savings = income - expenses
        return {"income": income, "expenses": expenses, "savings": savings}

    def monthly_analysis(self, year: int, month: int) -> Dict:
        """Return monthly totals per user, household totals, and category breakdown."""

        pattern = f"{year:04d}-{month:02d}-%"

        # Per-user aggregates
        per_user: Dict[int, Dict[str, float]] = {}

        users = self.conn.execute("SELECT id, name FROM users").fetchall()
        for user in users:
            user_id = int(user["id"])
            income = self._scalar(
                """
                SELECT COALESCE(SUM(amount), 0) FROM personal_transactions
                WHERE user_id = ? AND type = 'income' AND date LIKE ?
                """,
                (user_id, pattern),
            )
            personal_expenses = self._scalar(
                """
                SELECT COALESCE(SUM(amount), 0) FROM personal_transactions
                WHERE user_id = ? AND type = 'expense' AND date LIKE ?
                """,
                (user_id, pattern),
            )
            shared_owed = self._scalar(
                """
                SELECT COALESCE(SUM(ss.owed_amount), 0) FROM shared_splits ss
                JOIN shared_expenses se ON se.id = ss.expense_id
                WHERE ss.user_id = ? AND se.date LIKE ?
                """,
                (user_id, pattern),
            )

            total_spending = personal_expenses + shared_owed
            savings = income - total_spending

            per_user[user_id] = {
                "name": user["name"],
                "personal_income": income,
                "personal_expenses": personal_expenses,
                "shared_owed": shared_owed,
                "total_spending": total_spending,
                "savings": savings,
            }

        shared_total = self._scalar(
            """
            SELECT COALESCE(SUM(total_amount), 0) FROM shared_expenses WHERE date LIKE ?
            """,
            (pattern,),
        )
        personal_total = self._scalar(
            """
            SELECT COALESCE(SUM(amount), 0) FROM personal_transactions
            WHERE type = 'expense' AND date LIKE ?
            """,
            (pattern,),
        )

        # Category breakdown combines personal and shared shares.
        category_totals = defaultdict(float)

        personal_categories = self.conn.execute(
            """
            SELECT category, SUM(amount) as total FROM personal_transactions
            WHERE type = 'expense' AND date LIKE ?
            GROUP BY category
            """,
            (pattern,),
        )
        for row in personal_categories:
            category_totals[row["category"]] += float(row["total"])

        shared_categories = self.conn.execute(
            """
            SELECT se.category, ss.owed_amount FROM shared_expenses se
            JOIN shared_splits ss ON se.id = ss.expense_id
            WHERE se.date LIKE ?
            """,
            (pattern,),
        )
        for row in shared_categories:
            category_totals[row["category"]] += float(row["owed_amount"])

        return {
            "per_user": per_user,
            "household": {
                "shared_expense_total": shared_total,
                "personal_expense_total": personal_total,
                "combined_spending": personal_total + shared_total,
            },
            "categories": dict(category_totals),
        }

    # ------------------------
    # Internal utilities
    # ------------------------

    def _scalar(self, query: str, params: Optional[tuple] = None) -> float:
        cursor = self.conn.execute(query, params or ())
        value = cursor.fetchone()[0]
        return float(value) if value is not None else 0.0


__all__ = ["ExpenseTracker"]
