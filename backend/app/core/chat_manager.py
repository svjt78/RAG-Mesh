"""
Chat Session Manager for RAGMesh
Manages in-memory chat sessions with history compaction
"""

import uuid
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from app.core.models import ChatSession, ChatTurn, ChatHistory, ChatProfile, Answer
from app.adapters.base import LLMAdapter

logger = logging.getLogger(__name__)


class ChatSessionManager:
    """Manages in-memory chat sessions with automatic compaction"""

    def __init__(self, llm_adapter: LLMAdapter):
        """
        Initialize chat session manager

        Args:
            llm_adapter: LLM adapter for summarization
        """
        self.sessions: Dict[str, ChatSession] = {}
        self.llm = llm_adapter
        logger.info("ChatSessionManager initialized")

    def create_session(self, workflow_id: str, chat_profile_id: str) -> str:
        """
        Create new chat session

        Args:
            workflow_id: Workflow to use for this session
            chat_profile_id: Chat profile to use

        Returns:
            Generated session_id
        """
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            workflow_id=workflow_id,
            chat_profile_id=chat_profile_id
        )
        self.sessions[session_id] = session
        logger.info(f"Created chat session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get session by ID

        Args:
            session_id: Session identifier

        Returns:
            ChatSession if found, None otherwise
        """
        return self.sessions.get(session_id)

    def add_turn(
        self,
        session_id: str,
        query: str,
        answer: Answer,
        run_id: str,
        tokens: int
    ) -> int:
        """
        Add turn to session

        Args:
            session_id: Session identifier
            query: User query
            answer: Generated answer
            run_id: Associated run ID
            tokens: Total tokens used

        Returns:
            Turn number

        Raises:
            ValueError: If session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        turn_number = session.history.total_turns + 1
        turn = ChatTurn(
            turn_number=turn_number,
            query=query,
            answer=answer,
            run_id=run_id,
            tokens=tokens
        )

        session.history.turns.append(turn)
        session.history.total_turns = turn_number
        session.total_tokens += tokens
        session.last_updated = datetime.now()

        logger.info(f"Added turn {turn_number} to session {session_id} ({tokens} tokens)")
        return turn_number

    async def check_and_compact(
        self,
        session_id: str,
        profile: ChatProfile
    ) -> bool:
        """
        Check if compaction needed and perform it

        Args:
            session_id: Session identifier
            profile: Chat profile with compaction settings

        Returns:
            True if compaction was performed, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found for compaction: {session_id}")
            return False

        # Calculate current history tokens
        history_tokens = sum(turn.tokens for turn in session.history.turns)

        # Check if compaction needed
        needs_compaction = (
            history_tokens > profile.compaction_threshold_tokens or
            len(session.history.turns) > profile.max_history_turns
        )

        if needs_compaction:
            logger.info(
                f"Compacting session {session_id}: "
                f"{history_tokens} tokens, {len(session.history.turns)} turns"
            )
            await self._compact_history(session, profile)
            return True

        return False

    async def _compact_history(self, session: ChatSession, profile: ChatProfile):
        """
        Compact older turns into summary using LLM

        Args:
            session: Chat session to compact
            profile: Chat profile with compaction settings
        """
        # Keep last N turns, summarize the rest
        keep_turns = max(1, profile.max_history_turns // 2)

        if len(session.history.turns) <= keep_turns:
            logger.info(f"No compaction needed: only {len(session.history.turns)} turns")
            return

        turns_to_summarize = session.history.turns[:-keep_turns]
        kept_turns = session.history.turns[-keep_turns:]

        # Build conversation text for summarization
        conversation_text = ""
        for turn in turns_to_summarize:
            conversation_text += f"User: {turn.query}\n"
            conversation_text += f"Assistant: {turn.answer.answer}\n\n"

        # Generate summary
        summary_prompt = f"""Summarize the following conversation history concisely.
Focus on key topics discussed, important facts mentioned, and context needed for future questions.

Conversation:
{conversation_text}

Provide a brief summary (max {profile.summarization_max_tokens} tokens):"""

        try:
            response = await self.llm.generate(
                prompt=summary_prompt,
                system_prompt="You are a helpful assistant that summarizes conversations.",
                temperature=0.0,
                max_tokens=profile.summarization_max_tokens
            )

            summary = response["content"]

            # Update session
            session.history.summary = summary
            session.history.summary_covers_turns = [t.turn_number for t in turns_to_summarize]
            session.history.turns = kept_turns

            logger.info(
                f"Compacted {len(turns_to_summarize)} turns into summary "
                f"for session {session.session_id}"
            )

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # Fallback: just drop oldest turns without summary
            session.history.turns = kept_turns
            logger.warning(f"Fell back to dropping {len(turns_to_summarize)} oldest turns")

    def get_formatted_history(
        self,
        session_id: str,
        profile: ChatProfile,
        encoding
    ) -> Tuple[str, int]:
        """
        Get formatted chat history for context

        Args:
            session_id: Session identifier
            profile: Chat profile
            encoding: Tiktoken encoding for token counting

        Returns:
            Tuple of (formatted_text, token_count)
        """
        session = self.sessions.get(session_id)
        if not session:
            return "", 0

        history_parts = []

        # Add summary if exists
        if session.history.summary and profile.include_summary_in_context:
            history_parts.append("[Previous conversation summary]")
            history_parts.append(session.history.summary)
            history_parts.append("")

        # Add recent turns
        if session.history.turns:
            history_parts.append("[Recent conversation]")
            for turn in session.history.turns:
                history_parts.append(f"User: {turn.query}")
                history_parts.append(f"Assistant: {turn.answer.answer}")
                history_parts.append("")

        history_text = "\n".join(history_parts)

        # Count tokens
        try:
            tokens = len(encoding.encode(history_text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            tokens = len(history_text) // 4  # Fallback estimate

        return history_text, tokens

    def delete_session(self, session_id: str):
        """
        Delete session

        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")

    def check_quit_command(self, query: str) -> bool:
        """
        Check if query is a quit command

        Args:
            query: User query

        Returns:
            True if quit command, False otherwise
        """
        return query.strip().lower() == "quit"

    def get_session_count(self) -> int:
        """
        Get number of active sessions

        Returns:
            Session count
        """
        return len(self.sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session information summary

        Args:
            session_id: Session identifier

        Returns:
            Session info dict or None
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "total_turns": session.history.total_turns,
            "total_tokens": session.total_tokens,
            "created_at": session.created_at.isoformat(),
            "last_updated": session.last_updated.isoformat(),
            "has_summary": session.history.summary is not None,
            "current_turns_count": len(session.history.turns)
        }
