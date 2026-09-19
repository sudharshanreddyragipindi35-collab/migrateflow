from app.ingestion.models import ColumnProfile, SourceFileProfile
from app.mapping.engine import DeterministicFallback, InvalidModelOutput, propose_mappings
from app.mapping.models import ModelMapping
from app.mapping.schema import load_target_schema


def column(name: str, kind: str = "string", unique: float = 1.0) -> ColumnProfile:
    return ColumnProfile(
        name=name,
        inferred_type=kind,
        null_ratio=0,
        unique_ratio=unique,
        masked_samples=["masked"],
        likely_identifier=unique == 1,
        date_patterns=[],
    )


def test_obvious_alias_has_high_inspectable_confidence() -> None:
    profile = SourceFileProfile(
        file_name="employees.csv", sheet_name=None, row_count=2,
        columns=[column("staff_id")], duplicate_row_count=0, encoding="utf-8",
    )
    proposal = propose_mappings([profile], load_target_schema(), DeterministicFallback())[0]
    assert proposal.target_field == "employee_id"
    assert proposal.confidence >= 0.9
    assert proposal.evidence.alias_match == 1
    assert proposal.provider == "deterministic_fallback"
    assert "MODEL_FALLBACK" in proposal.warnings


def test_ambiguous_column_has_alternatives() -> None:
    profile = SourceFileProfile(
        file_name="employees.csv", sheet_name=None, row_count=2,
        columns=[column("person_value")], duplicate_row_count=0, encoding="utf-8",
    )
    proposal = propose_mappings([profile], load_target_schema(), DeterministicFallback())[0]
    assert proposal.requires_human
    assert proposal.alternatives


class CollisionModel:
    provider = "test"

    def propose(self, source_file: str, item: ColumnProfile, schema: object) -> ModelMapping:
        return ModelMapping(target_field="email", confidence=1, alternatives=[], reasoning="test")


def test_target_collisions_are_detected() -> None:
    profile = SourceFileProfile(
        file_name="employees.csv", sheet_name=None, row_count=2,
        columns=[column("work_email", "email"), column("personal_email", "email")],
        duplicate_row_count=0, encoding="utf-8",
    )
    proposals = propose_mappings([profile], load_target_schema(), CollisionModel())
    assert all(item.collision and item.requires_human for item in proposals)


class InvalidModel:
    provider = "invalid"

    def propose(self, source_file: str, item: ColumnProfile, schema: object) -> ModelMapping:
        raise InvalidModelOutput("invalid structured response")


def test_invalid_model_output_fails_safely() -> None:
    profile = SourceFileProfile(
        file_name="employees.csv", sheet_name=None, row_count=1,
        columns=[column("email", "email")], duplicate_row_count=0, encoding="utf-8",
    )
    try:
        propose_mappings([profile], load_target_schema(), InvalidModel())
    except InvalidModelOutput as exc:
        assert "structured" in str(exc)
    else:
        raise AssertionError("invalid output must not be accepted")

