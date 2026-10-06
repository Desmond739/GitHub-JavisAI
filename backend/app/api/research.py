from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.account import current_user
from app.product.billing import billing_service
from app.product.research import research_service

router = APIRouter()


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@router.post("/research")
def research(request: ResearchRequest, user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    user_id = str(user["id"])
    quote = billing_service.quote_conversation(user_id)
    if not quote["allowed"]:
        raise HTTPException(status_code=402, detail="Add wallet funds to continue research.")
    try:
        result = research_service.answer(request.question)
        billing_service.record_conversation(user_id)
        result["charged_xaf"] = quote["charge_xaf"]
        return result
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
