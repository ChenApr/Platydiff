"""Project-defined domain failures converted at the pipeline boundary."""

from __future__ import annotations

from platydiff.core.models import JsonObject, PipelineStage


class DomainError(Exception):
    """An expected comparison-domain failure."""

    code: str
    status_code: int
    stage: PipelineStage
    details: JsonObject
    retryable: bool

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int,
        stage: PipelineStage,
        details: JsonObject | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.stage = stage
        self.details = {} if details is None else details
        self.retryable = retryable


class InvalidSpecError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="invalid_spec",
            status_code=400,
            stage=PipelineStage.VALIDATING,
        )


class SourceNotFoundError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="source_not_found",
            status_code=404,
            stage=PipelineStage.SOURCING,
        )


class SourcePermissionError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="permission_denied",
            status_code=403,
            stage=PipelineStage.SOURCING,
        )


class ResourceLimitError(DomainError):
    def __init__(self, message: str, *, stage: PipelineStage) -> None:
        super().__init__(
            message,
            code="resource_limit_exceeded",
            status_code=413,
            stage=stage,
        )


class UnsupportedEncodingError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="unsupported_encoding",
            status_code=415,
            stage=PipelineStage.DECODING,
        )


class DecodeError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="decode_error",
            status_code=422,
            stage=PipelineStage.DECODING,
        )


class CompareResourceLimitError(DomainError):
    def __init__(self, message: str, *, used: int, limit: int) -> None:
        super().__init__(
            message,
            code="compare_resource_limit",
            status_code=413,
            stage=PipelineStage.COMPARING,
            details={"used": used, "limit": limit},
        )


class InputOutputError(DomainError):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool = True,
        stage: PipelineStage = PipelineStage.SOURCING,
    ) -> None:
        super().__init__(
            message,
            code="io_error",
            status_code=500,
            stage=stage,
            retryable=retryable,
        )


class SourceChangedError(DomainError):
    """A source changed after its snapshot was established."""

    def __init__(self, *, stage: PipelineStage) -> None:
        if stage not in (
            PipelineStage.DETECTING,
            PipelineStage.DECODING,
            PipelineStage.COMPARING,
        ):
            raise ValueError("source changes must be reported at an observing stage")
        super().__init__(
            "A source changed while it was being compared.",
            code="source_changed",
            status_code=409,
            stage=stage,
        )
