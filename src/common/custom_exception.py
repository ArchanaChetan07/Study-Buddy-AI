"""
custom_exception.py — Structured exception with file/line info.
"""
import sys
import traceback


class CustomException(Exception):
    """
    Wraps an exception with additional context:
    the original message, the underlying error, and source location.

    Usage:
        raise CustomException("LLM call failed", original_exc)
    """

    def __init__(self, message: str, error_detail: Exception | None = None):
        self.error_message = self._build_message(message, error_detail)
        super().__init__(self.error_message)

    @staticmethod
    def _build_message(message: str, error_detail: Exception | None) -> str:
        _, _, exc_tb = sys.exc_info()

        if exc_tb is not None:
            file_name = exc_tb.tb_frame.f_code.co_filename
            line_number = exc_tb.tb_lineno
        else:
            file_name = "unknown"
            line_number = "unknown"

        detail_str = str(error_detail) if error_detail else "—"
        return (
            f"{message} | "
            f"Cause: {detail_str} | "
            f"File: {file_name} | "
            f"Line: {line_number}"
        )

    def __str__(self) -> str:
        return self.error_message
