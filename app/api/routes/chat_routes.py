from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_consultation_workflow
from app.domain.workflows.consultation_workflow import ConsultationWorkflow
from app.schemas.chat_schemas import ChatRequest, ChatStartResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/start", response_model=ChatStartResponse)
async def start_chat(
    patient_id: int = Query(...),
    workflow: ConsultationWorkflow = Depends(get_consultation_workflow),
):
    conversation = await workflow.start_conversation(patient_id, channel="web")
    return ChatStartResponse(conversation_id=conversation.id)


@router.post("")
async def chat(
    body: ChatRequest,
    patient_id: int = Query(...),
    workflow: ConsultationWorkflow = Depends(get_consultation_workflow),
):
    import sys
    print(f"[chat] received request patient_id={patient_id}, message={body.message!r}", flush=True)
    if not body.conversation_id:
        print("[chat] creating new conversation...", flush=True)
        conversation = await workflow.start_conversation(patient_id, channel="web")
        conversation_id = conversation.id
        print(f"[chat] conversation created id={conversation_id}", flush=True)
    else:
        conversation_id = body.conversation_id
        print(f"[chat] using existing conversation_id={conversation_id}", flush=True)

    async def event_generator():
        async for delta in workflow.chat_stream(
            patient_id=patient_id,
            conversation_id=conversation_id,
            user_message=body.message,
            channel="web",
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
