"""
Unit tests for Hallucination check
"""

from unittest.mock import AsyncMock

import pytest

from app.core.models import Answer, Citation
from app.modules.judge.checks.hallucination import HallucinationCheck


@pytest.mark.unit
class TestHallucinationCheck:
    """Test cases for Hallucination check."""

    @pytest.fixture
    def check(self, mock_llm_adapter: AsyncMock) -> HallucinationCheck:
        """Create a HallucinationCheck instance."""
        config = {"threshold": 0.1, "use_llm": True}  # Low threshold = less tolerance
        return HallucinationCheck(config=config, llm_adapter=mock_llm_adapter)

    @pytest.mark.asyncio
    async def test_no_hallucination(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test answer without hallucinations."""
        answer = Answer(
            answer_text="The policy provides Coverage A for dwelling as stated in the document [1].",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        # Mock LLM to indicate no hallucination
        mock_llm_adapter.generate.return_value = (
            "NO_HALLUCINATION\nScore: 0.0\nAll claims are supported by citations."
        )

        result = await check.validate(
            query="What does the policy cover?",
            answer=answer,
        )

        assert result.passed is True
        assert result.score == 0.0  # 0.0 = no hallucination

    @pytest.mark.asyncio
    async def test_hallucination_detected(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test answer with fabricated information."""
        answer = Answer(
            answer_text="The policy covers nuclear war damage and alien invasion [1].",
            citations=sample_citations,  # Citations don't mention these
            confidence="low",
            assumptions=[],
            limitations=[],
        )

        # Mock LLM to detect hallucination
        mock_llm_adapter.generate.return_value = (
            "HALLUCINATION_DETECTED\nScore: 0.8\n"
            "Nuclear war and alien invasion are not mentioned in citations."
        )

        result = await check.validate(
            query="What is covered?",
            answer=answer,
        )

        assert result.passed is False
        assert result.score > 0.1  # Above threshold
        assert "hallucination" in result.details.get("message", "").lower() or len(result.details) > 0

    @pytest.mark.asyncio
    async def test_minor_hallucination(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test answer with minor unsupported details."""
        answer = Answer(
            answer_text="The policy provides $500,000 dwelling coverage [1], typically paid within 30 days.",
            citations=sample_citations,  # "30 days" not in citations
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        # Mock LLM to detect minor hallucination
        mock_llm_adapter.generate.return_value = (
            "MINOR_HALLUCINATION\nScore: 0.15\n"
            "The 30-day timeframe is not supported by citations."
        )

        result = await check.validate(
            query="What is the dwelling coverage?",
            answer=answer,
        )

        assert result.passed is False  # 0.15 > 0.1 threshold
        assert result.score == pytest.approx(0.15, abs=0.05)

    @pytest.mark.asyncio
    async def test_no_citations(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test answer without any citations."""
        answer = Answer(
            answer_text="The policy provides comprehensive coverage.",
            citations=[],
            confidence="low",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="What is covered?",
            answer=answer,
        )

        # Cannot verify hallucination without citations
        # Should be treated as potential hallucination
        assert result.passed is False
        assert result.score > 0.0

    @pytest.mark.asyncio
    async def test_numeric_hallucination(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test hallucination involving specific numbers."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Coverage A: Dwelling - $500,000",
                score=0.9,
                metadata={},
            )
        ]

        answer = Answer(
            answer_text="The dwelling coverage is $750,000 [1].",
            citations=citations,  # Says $500,000 not $750,000
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = (
            "HALLUCINATION\nScore: 0.9\n"
            "Answer states $750,000 but citation says $500,000."
        )

        result = await check.validate(
            query="What is the dwelling limit?",
            answer=answer,
        )

        assert result.passed is False
        assert result.score > 0.5  # High hallucination score

    @pytest.mark.asyncio
    async def test_llm_response_parsing(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test parsing various LLM response formats."""
        answer = Answer(
            answer_text="Test answer [1]",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        test_cases = [
            ("Hallucination score: 0.0", 0.0, True),
            ("Score: 0.05 - Minimal hallucination", 0.05, True),
            ("HALLUCINATION: 0.2", 0.2, False),
            ("Severe hallucination detected. Score: 0.9", 0.9, False),
        ]

        for llm_response, expected_score, should_pass in test_cases:
            mock_llm_adapter.generate.return_value = llm_response
            result = await check.validate(query="Test", answer=answer)

            assert result.score == pytest.approx(expected_score, abs=0.05)
            assert result.passed == should_pass

    @pytest.mark.asyncio
    async def test_threshold_configuration(
        self,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test different threshold configurations."""
        answer = Answer(
            answer_text="Test answer [1]",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = "Score: 0.15"

        # Strict threshold (0.1)
        strict_check = HallucinationCheck(
            config={"threshold": 0.1, "use_llm": True},
            llm_adapter=mock_llm_adapter,
        )
        result = await strict_check.validate(query="Test", answer=answer)
        assert result.passed is False  # 0.15 > 0.1

        # Lenient threshold (0.2)
        lenient_check = HallucinationCheck(
            config={"threshold": 0.2, "use_llm": True},
            llm_adapter=mock_llm_adapter,
        )
        result = await lenient_check.validate(query="Test", answer=answer)
        assert result.passed is True  # 0.15 < 0.2

    @pytest.mark.asyncio
    async def test_systematic_hallucination(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test answer that is entirely fabricated."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Section I - Exclusions: Water damage, earth movement.",
                score=0.9,
                metadata={},
            )
        ]

        answer = Answer(
            answer_text="The policy provides unlimited worldwide coverage for all perils [1].",
            citations=citations,  # Citation is about exclusions, not unlimited coverage
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = (
            "SEVERE_HALLUCINATION\nScore: 1.0\n"
            "Answer completely contradicts the citation content."
        )

        result = await check.validate(
            query="What does the policy cover?",
            answer=answer,
        )

        assert result.passed is False
        assert result.score >= 0.9  # Very high hallucination

    @pytest.mark.asyncio
    async def test_extrapolation_vs_hallucination(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test reasonable extrapolation vs actual hallucination."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Coverage A protects your dwelling and attached structures.",
                score=0.9,
                metadata={},
            )
        ]

        # Reasonable extrapolation
        answer1 = Answer(
            answer_text="Coverage A protects your home's main structure [1].",
            citations=citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = (
            "Score: 0.05\nReasonable interpretation of dwelling."
        )

        result = await check.validate(query="What is covered?", answer=answer1)
        assert result.passed is True

        # Actual hallucination
        answer2 = Answer(
            answer_text="Coverage A includes your boats and aircraft [1].",
            citations=citations,
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = (
            "Score: 0.8\nBoats and aircraft not mentioned."
        )

        result = await check.validate(query="What is covered?", answer=answer2)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_citation_misattribution(
        self,
        check: HallucinationCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test when answer attributes wrong info to a citation."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Coverage A: Dwelling - $500,000",
                score=0.9,
                metadata={},
            ),
            Citation(
                chunk_id="chunk2",
                doc_id="doc123",
                text="Coverage B: Other Structures - $50,000",
                score=0.85,
                metadata={},
            ),
        ]

        answer = Answer(
            answer_text="Coverage A provides $50,000 for other structures [1].",
            citations=citations,  # Mixing up [1] and [2]
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = (
            "Score: 0.7\nIncorrect attribution - confusing Coverage A with B."
        )

        result = await check.validate(
            query="What does Coverage A provide?",
            answer=answer,
        )

        assert result.passed is False
        assert result.score > 0.5
