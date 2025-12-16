import logging
import uuid
from typing import Optional

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai.types import Content, Part

from ally.ai.agents.competitor_report import competitor_report_agent

logger = logging.getLogger(__name__)


class AgentService:
    """Service for running AI agents with proper session management."""

    @staticmethod
    async def run_competitor_report(
        product_id: str,
        user_id: str = 'default_user',
        timeout_seconds: int = 300
    ) -> str:
        """
        Run the competitor report agent for a specific product.

        Args:
            product_id: The product ID to analyze
            user_id: The user ID for the session
            timeout_seconds: Maximum time to wait for completion (default: 300 seconds / 5 minutes)

        Returns:
            The generated competitor report as a string

        Raises:
            ValueError: If the product_id is invalid or agent fails
            TimeoutError: If the agent execution exceeds the timeout
        """
        logger.info(f'Starting competitor report for product: {product_id}')

        # Create the agent
        agent = competitor_report_agent(product_id)
        agent_name = "competitor_report_agent"

        # Create session service (in-memory)
        session_service = InMemorySessionService()

        # Create a new session
        session_id = str(uuid.uuid4())
        logger.info(f'Creating session: {session_id}')

        await session_service.create_session(
            app_name=agent_name,
            user_id=user_id,
            session_id=session_id,
            state={
                "user_id": user_id,
                "product_id": product_id,
            },
        )

        logger.info(f'Session created: {session_id}')

        # Create the runner with in-memory services
        runner = Runner(
            agent=agent,
            app_name=agent_name,
            session_service=session_service,
            artifact_service=InMemoryArtifactService(),
            memory_service=InMemoryMemoryService(),
        )

        logger.info('Starting agent execution')

        # Prepare the user message as a Content object
        message_text = f"Generate a comprehensive competitor report for product ID: {product_id}"
        user_message = Content(
            role="user",
            parts=[Part(text=message_text)]
        )

        # Run the agent and collect events
        events = []
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
                run_config=RunConfig(streaming_mode=StreamingMode.NONE),
            ):
                events.append(event)
                logger.debug(f'Received event: {event.type if hasattr(event, "type") else type(event).__name__}')

        except Exception as e:
            logger.error(f'Error during agent execution: {str(e)}', exc_info=True)
            raise ValueError(f'Agent execution failed: {str(e)}')

        # Extract the final response from events
        report = AgentService._extract_final_response(events)

        logger.info(f'Agent execution completed. Generated {len(events)} events.')

        return report

    @staticmethod
    def _extract_final_response(events) -> str:
        """
        Extract the final agent response from the event stream.

        Args:
            events: List of events from the agent runner

        Returns:
            The final response text
        """
        if events:
            final_event = events[-1]
            if hasattr(final_event, 'content') and final_event.content:
                content_obj = final_event.content
                if hasattr(content_obj, 'parts') and content_obj.parts:
                    response_text = content_obj.parts[0].text if hasattr(content_obj.parts[0], 'text') else str(content_obj.parts[0])
                    return response_text
            return str(final_event)
        return 'No response generated'
