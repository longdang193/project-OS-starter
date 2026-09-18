"""Compatibility exports for runtime contract."""
try:
    from project_os_runtime.results import (
        encode_result_receipt,
        parse_result_receipt,
        validate_task_result,
        encode_task_result,
        publish_task_result,
        parse_task_result,
        RESULT_SCHEMA,
        RESULT_MAX_BYTES,
        RESULT_MAX_AGE_SECONDS,
        WORKER_STATES,
        CLEANUP_STATES,
        DESCENDANT_STATES,
        TASK_RESULT_SCHEMA,
        TASK_RESULT_MAX_BYTES,
        TASK_RESULT_STATUSES,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.results import (
        encode_result_receipt,
        parse_result_receipt,
        validate_task_result,
        encode_task_result,
        publish_task_result,
        parse_task_result,
        RESULT_SCHEMA,
        RESULT_MAX_BYTES,
        RESULT_MAX_AGE_SECONDS,
        WORKER_STATES,
        CLEANUP_STATES,
        DESCENDANT_STATES,
        TASK_RESULT_SCHEMA,
        TASK_RESULT_MAX_BYTES,
        TASK_RESULT_STATUSES,
    )

__all__ = ['encode_result_receipt', 'parse_result_receipt', 'validate_task_result', 'encode_task_result', 'publish_task_result', 'parse_task_result', 'RESULT_SCHEMA', 'RESULT_MAX_BYTES', 'RESULT_MAX_AGE_SECONDS', 'WORKER_STATES', 'CLEANUP_STATES', 'DESCENDANT_STATES', 'TASK_RESULT_SCHEMA', 'TASK_RESULT_MAX_BYTES', 'TASK_RESULT_STATUSES']
