"""The household's saved resilience plan (contract §11.11). Every query is by one account id."""

from dataclasses import dataclass

from sqlalchemy import Boolean, delete, func, literal_column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import ReturningInsert

from app.models.resilience_plan import ResiliencePlan

FOREIGN_KEY_VIOLATION = "23503"


class AccountGoneError(Exception):
    """The plan's account no longer exists (deleted after its token was checked)."""


@dataclass(frozen=True, slots=True)
class PlanInputs:
    monthly_income: int
    monthly_essentials: int
    savings: int
    shock_type: str
    income_reduction_pct: int | None
    duration_months: int
    shock_amount: int | None
    coping_levers: list[str]


class ResiliencePlanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, account_id: str) -> ResiliencePlan | None:
        return self._session.get(ResiliencePlan, account_id)

    def save(self, account_id: str, inputs: PlanInputs) -> tuple[ResiliencePlan, bool]:
        """Insert the plan, or replace the account's plan, in one statement (no read first).

        Returns the stored row and whether it was created (`xmax = 0` holds only for a row this
        statement inserted). Two concurrent saves both succeed; the later one wins.
        """
        values = {
            "account_id": account_id,
            "monthly_income": inputs.monthly_income,
            "monthly_essentials": inputs.monthly_essentials,
            "savings": inputs.savings,
            "shock_type": inputs.shock_type,
            "income_reduction_pct": inputs.income_reduction_pct,
            "duration_months": inputs.duration_months,
            "shock_amount": inputs.shock_amount,
            "coping_levers": inputs.coping_levers,
        }
        statement: ReturningInsert[ResiliencePlan, bool] = (
            insert(ResiliencePlan)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[ResiliencePlan.account_id],
                set_={
                    **{key: value for key, value in values.items() if key != "account_id"},
                    "updated_at": func.now(),
                },
            )
            .returning(ResiliencePlan, literal_column("xmax = 0", Boolean).label("created"))
            .execution_options(populate_existing=True)
        )
        try:
            plan, created = self._session.execute(statement).one()
        except IntegrityError as error:
            self._session.rollback()
            # Only the account's foreign key: a CHECK failure is a bug and must surface as one.
            if getattr(error.orig, "sqlstate", None) == FOREIGN_KEY_VIOLATION:
                raise AccountGoneError from error
            raise
        self._session.commit()
        return plan, bool(created)

    def delete(self, account_id: str) -> bool:
        result = self._session.execute(
            delete(ResiliencePlan)
            .where(ResiliencePlan.account_id == account_id)
            .returning(ResiliencePlan.account_id)
        )
        deleted = result.first() is not None
        self._session.commit()
        return deleted
