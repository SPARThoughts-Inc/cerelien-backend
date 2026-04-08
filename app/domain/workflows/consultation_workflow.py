import logging
import os

from agents import RunConfig, Runner
from agents.models.openai_provider import OpenAIProvider
from openai import AsyncOpenAI

from app.domain.business_process.agents.consultation_agent import consultation_agent
from app.domain.business_process.agents.context import ConsultationContext
from app.domain.entities.conversation_entity import Conversation
from app.domain.entities.message_entity import Message
from app.domain.interfaces.conversation_repository import ConversationRepository
from app.domain.workflows.patient_workflow import PatientWorkflow

logger = logging.getLogger(__name__)


def _make_run_config() -> RunConfig:
    """Create a fresh RunConfig with an explicitly constructed OpenAI client.

    This avoids the bug where the agents SDK's lazy client initialization
    fails to find the API key inside uvicorn's async event loop.
    """
    key = os.environ.get("OPENAI_API_KEY", "")
    print(f"[_make_run_config] key len={len(key)}, key[:20]={key[:20]}", flush=True)
    client = AsyncOpenAI(api_key=key)
    provider = OpenAIProvider(openai_client=client)
    config = RunConfig(model_provider=provider, tracing_disabled=True)
    print(f"[_make_run_config] provider type={type(config.model_provider).__name__}", flush=True)
    return config


class ConsultationWorkflow:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        patient_workflow: PatientWorkflow,
    ):
        self.conversation_repo = conversation_repo
        self.patient_workflow = patient_workflow

    async def start_conversation(self, patient_id: int, channel: str = "web") -> Conversation:
        """Create a new conversation for the patient."""
        conversation = Conversation(
            id=0,  # Will be assigned by DB via SERIAL
            patient_id=patient_id,
            channel=channel,
        )
        return await self.conversation_repo.create(conversation)

    async def chat(
        self,
        patient_id: int,
        conversation_id: int,
        user_message: str,
        channel: str = "web",
    ) -> str:
        """Non-streaming chat: runs the agent and returns the final response."""
        # Save user message
        await self.conversation_repo.add_message(
            Message(
                id=0,  # Will be assigned by DB
                conversation_id=conversation_id,
                role="user",
                content=user_message,
            )
        )

        # Build context
        context = ConsultationContext(
            patient_id=str(patient_id),
            patient_workflow=self.patient_workflow,
            channel=channel,
        )

        # Build conversation history
        history = await self._build_history(conversation_id)

        # Run agent
        result = await Runner.run(
            starting_agent=consultation_agent,
            input=history,
            context=context,
            run_config=_make_run_config(),
        )

        assistant_text = result.final_output

        # Save assistant message
        await self.conversation_repo.add_message(
            Message(
                id=0,  # Will be assigned by DB
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_text,
            )
        )

        return assistant_text

    async def chat_stream(
        self,
        patient_id: int,
        conversation_id: int,
        user_message: str,
        channel: str = "web",
    ):
        """Streaming chat: yields text deltas as they arrive."""
        print(f"[chat_stream] START patient_id={patient_id}, conv_id={conversation_id}", flush=True)

        # Save user message
        await self.conversation_repo.add_message(
            Message(
                id=0,  # Will be assigned by DB
                conversation_id=conversation_id,
                role="user",
                content=user_message,
            )
        )
        print("[chat_stream] user message saved", flush=True)

        # Build context
        context = ConsultationContext(
            patient_id=str(patient_id),
            patient_workflow=self.patient_workflow,
            channel=channel,
        )

        # Build conversation history
        history = await self._build_history(conversation_id)
        print(f"[chat_stream] history built, {len(history)} messages", flush=True)

        # Run streamed
        run_cfg = _make_run_config()
        print(f"[chat_stream] run_config created, provider={type(run_cfg.model_provider).__name__}", flush=True)

        result = Runner.run_streamed(
            starting_agent=consultation_agent,
            input=history,
            context=context,
            run_config=run_cfg,
        )
        print("[chat_stream] Runner.run_streamed called, streaming events...", flush=True)

        full_response = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                delta = event.data.delta
                if delta:
                    full_response += delta
                    yield delta

        # Save the full assistant response after streaming completes
        await self.conversation_repo.add_message(
            Message(
                id=0,  # Will be assigned by DB
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
            )
        )

    async def _build_history(self, conversation_id: int) -> list[dict]:
        """Build message history for the agent from stored messages."""
        messages = await self.conversation_repo.get_messages(conversation_id)
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
            })
        return history
