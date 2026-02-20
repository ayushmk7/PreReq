"""CSV parsing and validation services for scores and question-concept mapping files."""

import io
from typing import Optional

import pandas as pd

from app.schemas.schemas import ValidationError
from app.services.validation_service import validate_file_limits


async def validate_scores_csv(
    file_content: bytes,
) -> tuple[Optional[pd.DataFrame], list[ValidationError]]:
    """Validate an exam scores CSV file per PRD §1.2.1.

    Required columns: StudentID, QuestionID, Score
    Optional column: MaxScore (defaults to 1.0)

    Returns:
        Tuple of (validated DataFrame or None, list of validation errors).
    """
    errors: list[ValidationError] = []

    # --- File-level limits ---
    limit_errors = validate_file_limits(file_content)
    if limit_errors:
        return None, limit_errors

    # --- Parse CSV ---
    try:
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        errors.append(ValidationError(message=f"Failed to parse CSV: {str(e)}"))
        return None, errors

    # --- Check required columns ---
    required = {"StudentID", "QuestionID", "Score"}
    missing = required - set(df.columns)
    if missing:
        errors.append(ValidationError(
            message=f"Missing required columns: {', '.join(sorted(missing))}"
        ))
        return None, errors

    # --- Default MaxScore ---
    if "MaxScore" not in df.columns:
        df["MaxScore"] = 1.0

    # --- Row-level validation ---
    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 1-indexed + header row

        # Non-null IDs
        if pd.isna(row["StudentID"]) or str(row["StudentID"]).strip() == "":
            errors.append(ValidationError(
                row=row_num, field="StudentID",
                message="StudentID must not be null or empty",
            ))

        if pd.isna(row["QuestionID"]) or str(row["QuestionID"]).strip() == "":
            errors.append(ValidationError(
                row=row_num, field="QuestionID",
                message="QuestionID must not be null or empty",
            ))

        # Score must be numeric
        try:
            score = float(row["Score"])
            max_score = float(row["MaxScore"])
        except (ValueError, TypeError):
            errors.append(ValidationError(
                row=row_num, field="Score",
                message="Score and MaxScore must be numeric",
            ))
            continue

        # MaxScore must be > 0
        if max_score <= 0:
            errors.append(ValidationError(
                row=row_num, field="MaxScore",
                message=f"MaxScore must be > 0, got {max_score}",
            ))

        # Score range: [0, MaxScore]
        if score < 0 or score > max_score:
            errors.append(ValidationError(
                row=row_num, field="Score",
                message=f"Score must be in [0, {max_score}], got {score}",
            ))

    # --- Duplicate check: (StudentID, QuestionID) ---
    if not errors:
        dupes = df[df.duplicated(subset=["StudentID", "QuestionID"], keep=False)]
        if not dupes.empty:
            seen = set()
            for idx, row in dupes.iterrows():
                key = (str(row["StudentID"]), str(row["QuestionID"]))
                if key not in seen:
                    errors.append(ValidationError(
                        row=int(idx) + 2,
                        field="StudentID,QuestionID",
                        message=f"Duplicate (StudentID={key[0]}, QuestionID={key[1]})",
                    ))
                    seen.add(key)

    if errors:
        return None, errors

    # Ensure string columns
    df["StudentID"] = df["StudentID"].astype(str).str.strip()
    df["QuestionID"] = df["QuestionID"].astype(str).str.strip()
    df["Score"] = df["Score"].astype(float)
    df["MaxScore"] = df["MaxScore"].astype(float)

    return df, errors


async def validate_mapping_csv(
    file_content: bytes,
    valid_question_ids: Optional[set[str]] = None,
) -> tuple[Optional[pd.DataFrame], list[ValidationError]]:
    """Validate a question-to-concept mapping CSV file per PRD §1.2.2.

    Required columns: QuestionID, ConceptID
    Optional column: Weight (defaults to 1.0)

    Returns:
        Tuple of (validated DataFrame or None, list of validation errors).
    """
    errors: list[ValidationError] = []

    # --- File-level limits ---
    limit_errors = validate_file_limits(file_content)
    if limit_errors:
        return None, limit_errors

    # --- Parse CSV ---
    try:
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        errors.append(ValidationError(message=f"Failed to parse CSV: {str(e)}"))
        return None, errors

    # --- Check required columns ---
    required = {"QuestionID", "ConceptID"}
    missing = required - set(df.columns)
    if missing:
        errors.append(ValidationError(
            message=f"Missing required columns: {', '.join(sorted(missing))}"
        ))
        return None, errors

    # --- Default Weight ---
    if "Weight" not in df.columns:
        df["Weight"] = 1.0

    # --- Row-level validation ---
    for idx, row in df.iterrows():
        row_num = int(idx) + 2

        if pd.isna(row["QuestionID"]) or str(row["QuestionID"]).strip() == "":
            errors.append(ValidationError(
                row=row_num, field="QuestionID",
                message="QuestionID must not be null or empty",
            ))

        if pd.isna(row["ConceptID"]) or str(row["ConceptID"]).strip() == "":
            errors.append(ValidationError(
                row=row_num, field="ConceptID",
                message="ConceptID must not be null or empty",
            ))

        try:
            weight = float(row["Weight"])
            if weight < 0:
                errors.append(ValidationError(
                    row=row_num, field="Weight",
                    message=f"Weight must be >= 0, got {weight}",
                ))
        except (ValueError, TypeError):
            errors.append(ValidationError(
                row=row_num, field="Weight",
                message="Weight must be numeric",
            ))

    # --- Cross-check: every QuestionID in mapping must exist in scores ---
    if not errors and valid_question_ids is not None:
        mapping_qids = set(df["QuestionID"].astype(str).str.strip())
        missing_qids = valid_question_ids - mapping_qids
        if missing_qids:
            errors.append(ValidationError(
                message=f"Questions in scores but not in mapping: {', '.join(sorted(missing_qids))}",
            ))

    if errors:
        return None, errors

    df["QuestionID"] = df["QuestionID"].astype(str).str.strip()
    df["ConceptID"] = df["ConceptID"].astype(str).str.strip()
    df["Weight"] = df["Weight"].astype(float)

    return df, errors
