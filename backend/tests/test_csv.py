"""Tests for CSV validation services — malformed file rejection per PRD §1.2."""

import pytest

from app.services.csv_service import validate_mapping_csv, validate_scores_csv


class TestScoresCSV:

    @pytest.mark.asyncio
    async def test_valid_csv(self):
        content = b"StudentID,QuestionID,Score,MaxScore\nS001,Q1,8,10\nS002,Q1,6,10\n"
        df, errors = await validate_scores_csv(content)
        assert df is not None
        assert len(errors) == 0
        assert len(df) == 2

    @pytest.mark.asyncio
    async def test_missing_columns(self):
        content = b"StudentID,Score\nS001,8\n"
        df, errors = await validate_scores_csv(content)
        assert df is None
        assert len(errors) > 0
        assert "QuestionID" in errors[0].message

    @pytest.mark.asyncio
    async def test_default_max_score(self):
        content = b"StudentID,QuestionID,Score\nS001,Q1,0.8\n"
        df, errors = await validate_scores_csv(content)
        assert df is not None
        assert float(df.iloc[0]["MaxScore"]) == 1.0

    @pytest.mark.asyncio
    async def test_null_student_id(self):
        content = b"StudentID,QuestionID,Score\n,Q1,8\n"
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_score_out_of_range(self):
        content = b"StudentID,QuestionID,Score,MaxScore\nS001,Q1,15,10\n"
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_negative_score(self):
        content = b"StudentID,QuestionID,Score,MaxScore\nS001,Q1,-1,10\n"
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_zero_max_score(self):
        content = b"StudentID,QuestionID,Score,MaxScore\nS001,Q1,0,0\n"
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_duplicate_student_question(self):
        content = b"StudentID,QuestionID,Score,MaxScore\nS001,Q1,8,10\nS001,Q1,9,10\n"
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0
        assert "Duplicate" in errors[0].message

    @pytest.mark.asyncio
    async def test_non_numeric_score(self):
        content = b"StudentID,QuestionID,Score\nS001,Q1,abc\n"
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_empty_file(self):
        content = b""
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_malformed_csv(self):
        content = b"not,a,valid\x00csv\nformat"
        df, errors = await validate_scores_csv(content)
        assert len(errors) > 0


class TestMappingCSV:

    @pytest.mark.asyncio
    async def test_valid_mapping(self):
        content = b"QuestionID,ConceptID,Weight\nQ1,C1,1.0\nQ1,C2,0.5\n"
        df, errors = await validate_mapping_csv(content)
        assert df is not None
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_missing_columns(self):
        content = b"QuestionID\nQ1\n"
        df, errors = await validate_mapping_csv(content)
        assert df is None
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_default_weight(self):
        content = b"QuestionID,ConceptID\nQ1,C1\n"
        df, errors = await validate_mapping_csv(content)
        assert df is not None
        assert float(df.iloc[0]["Weight"]) == 1.0

    @pytest.mark.asyncio
    async def test_negative_weight(self):
        content = b"QuestionID,ConceptID,Weight\nQ1,C1,-0.5\n"
        df, errors = await validate_mapping_csv(content)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_cross_validation(self):
        content = b"QuestionID,ConceptID\nQ1,C1\n"
        df, errors = await validate_mapping_csv(content, valid_question_ids={"Q1", "Q2"})
        assert len(errors) > 0
        assert "Q2" in errors[0].message

    @pytest.mark.asyncio
    async def test_null_concept_id(self):
        content = b"QuestionID,ConceptID\nQ1,\n"
        df, errors = await validate_mapping_csv(content)
        assert len(errors) > 0
