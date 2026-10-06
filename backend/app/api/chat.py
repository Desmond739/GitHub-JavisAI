from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import CHAT_MESSAGE_MAX_CHARACTERS
from app.services.assistant_core import (
    assistant_core,
)
from app.api.account import current_user
from app.product.billing import billing_service


router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=CHAT_MESSAGE_MAX_CHARACTERS,
    )


class ChatResponse(BaseModel):
    response: str
    charged_xaf: int = 0
    wallet_balance_xaf: int = 0


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    user: dict[str, object] = Depends(current_user),
) -> ChatResponse:
    user_id = str(user["id"])
    quote = billing_service.quote_conversation(user_id)
    if not quote["allowed"]:
        raise HTTPException(status_code=402, detail="Monthly conversations are used up. Add funds to continue at the disclosed rate of 10 XAF per message.")
    response = (
        assistant_core.respond(
            request.message
        )
    )
    try:
        account = billing_service.record_conversation(user_id)
    except PermissionError as error:
        raise HTTPException(status_code=402, detail=str(error)) from error
    return ChatResponse(
        response=response,
        charged_xaf=int(quote["charge_xaf"]),
        wallet_balance_xaf=int(account["wallet_balance_xaf"]),
    )
