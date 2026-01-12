"""
Unit tests for Citation Coverage check
"""

import pytest

from app.core.models import Answer, Citation
from app.modules.judge.checks.citation_coverage import CitationCoverageCheck


@pytest.mark.unit
class TestCitationCoverageCheck:
    """Test cases for Citation Coverage check."""

    @pytest.fixture
    def check(self) -> CitationCoverageCheck:
        """Create a CitationCoverageCheck instance."""
        config = {"threshold": 0.9}
        return CitationCoverageCheck(config=config)

    @pytest.fixture
    def sample_answer_with_citations(
        self, sample_citations: list[Citation]
    ) -> Answer:
        """Create a sample answer with proper citations."""
        return Answer(
            answer_text="The policy provides Coverage A for dwelling [1] and excludes water damage [2].",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

    @pytest.fixture
    def sample_answer_missing_citations(self) -> Answer:
        """Create an answer referencing non-existent citations."""
        return Answer(
            answer_text="The policy covers dwelling [1], personal property [2], and liability [3].",
            citations=[
                Citation(
                    chunk_id="chunk1",
                    doc_id="doc123",
                    text="Coverage A: Dwelling - $500,000",
                    score=0.95,
                    metadata={},
                )
            ],  # Only 1 citation but answer references [1], [2], [3]
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

    @pytest.mark.asyncio
    async def test_all_citations_present(
        self,
        check: CitationCoverageCheck,
        sample_answer_with_citations: Answer,
    ):
        """Test when all cited references exist."""
        result = await check.validate(
            query="What does the policy cover?",
            answer=sample_answer_with_citations,
        )

        assert result.passed is True
        assert result.score >= 0.9
        assert len(result.details.get("missing_citations", [])) == 0

    @pytest.mark.asyncio
    async def test_missing_citations(
        self,
        check: CitationCoverageCheck,
        sample_answer_missing_citations: Answer,
    ):
        """Test when some citations are missing."""
        result = await check.validate(
            query="What does the policy cover?",
            answer=sample_answer_missing_citations,
        )

        assert result.passed is False
        assert result.score < 0.9
        assert len(result.details.get("missing_citations", [])) > 0
        # Should identify [2] and [3] as missing
        missing = result.details["missing_citations"]
        assert "2" in missing or 2 in missing
        assert "3" in missing or 3 in missing

    @pytest.mark.asyncio
    async def test_no_citations_in_text(
        self, check: CitationCoverageCheck, sample_citations: list[Citation]
    ):
        """Test answer with no citation references in text."""
        answer = Answer(
            answer_text="The policy provides dwelling coverage and excludes water damage.",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="What does the policy cover?",
            answer=answer,
        )

        # No citations referenced in text, but citations provided
        # This should pass as there are no missing references
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_empty_citations_list(
        self, check: CitationCoverageCheck
    ):
        """Test answer with citation references but no citations provided."""
        answer = Answer(
            answer_text="The policy covers dwelling [1] and personal property [2].",
            citations=[],
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="What does the policy cover?",
            answer=answer,
        )

        assert result.passed is False
        assert result.score == 0.0
        assert len(result.details.get("missing_citations", [])) == 2

    @pytest.mark.asyncio
    async def test_multiple_citation_formats(
        self, check: CitationCoverageCheck, sample_citations: list[Citation]
    ):
        """Test different citation reference formats."""
        answer = Answer(
            answer_text="Coverage [1], exclusion [2], and additional info (see citation 1).",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="What is covered?",
            answer=answer,
        )

        # Should handle [1], [2] format
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_threshold_configuration(
        self, sample_answer_missing_citations: Answer
    ):
        """Test that threshold affects pass/fail decision."""
        # Strict threshold
        strict_check = CitationCoverageCheck(config={"threshold": 0.95})
        result = await strict_check.validate(
            query="Test", answer=sample_answer_missing_citations
        )
        assert result.passed is False

        # Lenient threshold
        lenient_check = CitationCoverageCheck(config={"threshold": 0.3})
        result = await lenient_check.validate(
            query="Test", answer=sample_answer_missing_citations
        )
        # Might pass with lenient threshold depending on coverage ratio
        # Score should be the same, only pass/fail changes
        assert result.score < 1.0

    @pytest.mark.asyncio
    async def test_citation_numbering_gaps(
        self, check: CitationCoverageCheck
    ):
        """Test handling of non-sequential citation numbers."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Text 1",
                score=0.9,
                metadata={},
            ),
            Citation(
                chunk_id="chunk5",
                doc_id="doc123",
                text="Text 5",
                score=0.85,
                metadata={},
            ),
        ]

        answer = Answer(
            answer_text="Coverage [1] and exclusion [5].",
            citations=citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="Test",
            answer=answer,
        )

        # Should correctly match [1] to first citation and [5] to second
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_duplicate_citation_references(
        self, check: CitationCoverageCheck, sample_citations: list[Citation]
    ):
        """Test handling duplicate citation references."""
        answer = Answer(
            answer_text="Coverage [1] is important. See [1] for details. Also [2].",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="Test",
            answer=answer,
        )

        # Duplicate references to [1] should be fine
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_high_coverage_score(self, check: CitationCoverageCheck):
        """Test perfect citation coverage."""
        citations = [
            Citation(
                chunk_id=f"chunk{i}",
                doc_id="doc123",
                text=f"Text {i}",
                score=0.9,
                metadata={},
            )
            for i in range(1, 6)
        ]

        answer = Answer(
            answer_text="Info [1], [2], [3], [4], and [5].",
            citations=citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="Test",
            answer=answer,
        )

        assert result.passed is True
        assert result.score == 1.0

    @pytest.mark.asyncio
    async def test_partial_coverage(self, check: CitationCoverageCheck):
        """Test partial citation coverage."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Text 1",
                score=0.9,
                metadata={},
            ),
            Citation(
                chunk_id="chunk2",
                doc_id="doc123",
                text="Text 2",
                score=0.85,
                metadata={},
            ),
        ]

        answer = Answer(
            answer_text="Coverage [1], [2], [3], and [4].",
            citations=citations,
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="Test",
            answer=answer,
        )

        # 2 out of 4 citations present = 50% coverage
        assert result.score == 0.5
        assert result.passed is False  # Below 0.9 threshold
