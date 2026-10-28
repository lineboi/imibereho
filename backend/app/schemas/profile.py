"""Household profile: `GET` and `PATCH /api/v1/user/profile` (contract §11.9).

The response is MISSING_APIS.pdf page 4's GET example, field for field. The PDF lists a `PUT`
for the update but gives it no body; the project owner chose `PATCH`, and its body is the
editable part of that same GET shape (everything but `id`), every field optional:

- a field left out is unchanged;
- `plannedEssentials` and `savingsBuffer` may be `null`, which clears them (they are `null`
  until first set, because register does not collect them);
- `null` for `district`, `householdSize`, `monthlyIncome` or `preferredLanguage` is 422
  `required`: those always have a value;
- an empty body `{}` changes nothing and returns the profile;
- anything else (including `id`, `identifier`, `password`, `currency`) is 422 `unknown_field`.

Bounds are the ones register uses. Identifier, password and currency are not part of the profile
the PDF shows, so this endpoint never changes them.
"""

from typing import Annotated, Final, Literal

from pydantic import Field, StrictInt, StrictStr, field_validator
from pydantic_core import PydanticCustomError

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN, MONEY_MAX
from app.schemas.auth import PreferredLanguage
from app.schemas.common import ApiModel, BodyModel

Money = Annotated[StrictInt, Field(ge=0, le=MONEY_MAX)]
UNSET_UNTIL_SET: Final = "Whole RWF; null until the household sets it"
# Fields that always hold a value: `null` is refused, while leaving them out is fine.
NON_NULLABLE: Final = ("district", "household_size", "monthly_income", "preferred_language")


class ProfileResponse(ApiModel):
    id: str
    district: str
    household_size: int
    monthly_income: int
    planned_essentials: int | None = Field(description=UNSET_UNTIL_SET)
    savings_buffer: int | None = Field(description=UNSET_UNTIL_SET)
    preferred_language: Literal["EN", "RW"]


class ProfilePatch(BodyModel):
    district: StrictStr | None = Field(
        default=None, max_length=32, description="A district code from /districts"
    )
    household_size: (
        Annotated[StrictInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)] | None
    ) = None
    monthly_income: Money | None = None
    planned_essentials: Money | None = Field(default=None, description="null clears it")
    savings_buffer: Money | None = Field(default=None, description="null clears it")
    preferred_language: PreferredLanguage | None = None

    @field_validator(*NON_NULLABLE, mode="before")
    @classmethod
    def _refuse_null(cls, value: object) -> object:
        # Runs only for fields the body contains (defaults are not validated), so leaving a
        # field out stays allowed; an explicit null maps to 422 `required` (contract §1.2).
        if value is None:
            raise PydanticCustomError("null_not_allowed", "This field cannot be null.")
        return value

    def changes(self) -> dict[str, object]:
        """The fields the body contained, by Python name, with their values (null included)."""
        return {name: getattr(self, name) for name in self.model_fields_set}
