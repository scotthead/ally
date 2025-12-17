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
from ally.ai.agents.recommendations import recommendations_agent
from ally.ai.agents.finalize import final_agent
from ally.services.competitor_report_service import competitor_report_service
from ally.services.product_recommendation_service import product_recommendation_service
from ally.services.summarization_service import summarization_service

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

        # Save the report using the CompetitorReportService
        competitor_report_service.save_report(product_id, report)
        logger.info(f'Saved competitor report for product: {product_id}')

        return report

    @staticmethod
    async def run_recommendations(
        product_id: str,
        user_id: str = 'default_user',
        timeout_seconds: int = 300
    ) -> str:
        """
        Run the recommendations agent for a specific product.

        Args:
            product_id: The product ID to analyze
            user_id: The user ID for the session
            timeout_seconds: Maximum time to wait for completion (default: 300 seconds / 5 minutes)

        Returns:
            The generated recommendations as a string

        Raises:
            ValueError: If the product_id is invalid or agent fails
            TimeoutError: If the agent execution exceeds the timeout
        """
        logger.info(f'Starting recommendations generation for product: {product_id}')

        # Load competitor report from service
        competitor_report = competitor_report_service.get_report(product_id)
        if competitor_report:
            logger.info(f'Loaded competitor report from service for product: {product_id}')
        else:
            logger.info(f'No competitor report found for product: {product_id}')

        # Create the agent
        agent = recommendations_agent(product_id, competitor_report)
        agent_name = "recommendations_agent"

        # Create session service (in-memory)
        session_service = InMemorySessionService()

        # Create a new session
        session_id = str(uuid.uuid4())
        logger.info(f'Creating session: {session_id}')

        # Include competitor report in session state
        session_state = {
            "user_id": user_id,
            "product_id": product_id,
        }

        if competitor_report:
            session_state["competitor_report"] = competitor_report

        await session_service.create_session(
            app_name=agent_name,
            user_id=user_id,
            session_id=session_id,
            state=session_state,
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
        message_text = f"Generate 3 actionable product optimization recommendations for product ID: {product_id}"
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
        recommendations = AgentService._extract_final_response(events)

        logger.info(f'Agent execution completed. Generated {len(events)} events.')

        # Save the recommendations using the ProductRecommendationService
        product_recommendation_service.save_recommendations(product_id, recommendations)
        logger.info(f'Saved recommendations for product: {product_id}')

        return recommendations

    @staticmethod
    async def run_final_agent(
        product_id: str,
        user_id: str = 'default_user',
        timeout_seconds: int = 600
    ) -> str:
        """
        Run the final agent to apply recommendations and create a summary.

        Args:
            product_id: The product ID to finalize
            user_id: The user ID for the session
            timeout_seconds: Maximum time to wait for completion (default: 600 seconds / 10 minutes)

        Returns:
            The final summarization report as a string

        Raises:
            ValueError: If the product_id is invalid or agent fails
            TimeoutError: If the agent execution exceeds the timeout
        """
        logger.info(f'Starting final agent for product: {product_id}')

        # Create the final sequential agent
        agent = final_agent(product_id)
        agent_name = "final_agent"

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

        logger.info('Starting final agent execution')

        # Prepare the user message as a Content object
        message_text = f"Finalize product updates and create summary for product ID: {product_id}"
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
        summary = AgentService._extract_final_response(events)

        logger.info(f'Agent execution completed. Generated {len(events)} events.')

        # Save the summary using the SummarizationService
        summarization_service.save_summarization(product_id, summary)
        logger.info(f'Saved summarization for product: {product_id}')

        return summary

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
