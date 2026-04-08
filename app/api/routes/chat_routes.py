from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_consultation_workflow
from app.domain.workflows.consultation_workflow import ConsultationWorkflow
from app.schemas.chat_schemas import ChatRequest, ChatStartResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/start", response_model=ChatStartResponse)
async def start_chat(
    patient_id: UUID = Query(...),
    workflow: ConsultationWorkflow = Depends(get_consultation_workflow),
):
    conversation = await workflow.start_conversation(patient_id, channel="web_chat")
    return ChatStartResponse(conversation_id=conversation.id)


@router.post("")
async def chat(
    body: ChatRequest,
    patient_id: UUID = Query(...),
    workflow: ConsultationWorkflow = Depends(get_consultation_workflow),
):
    if not body.conversation_id:
        conversation = await workflow.start_conversation(patient_id, channel="web_chat")
        conversation_id = conversation.id
    else:
        conversation_id = body.conversation_id

    async def event_generator():
        async for delta in workflow.chat_stream(
            patient_id=patient_id,
            conversation_id=conversation_id,
            user_message=body.message,
            channel="web_chat",
        ):
            yield f"data: {delta}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
