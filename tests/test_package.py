from packaging.version import Version

import un_schema_qa
from un_schema_qa.exceptions import (
    ConfigurationError,
    InputFormatError,
    ToolkitError,
    ValidationExecutionError,
    WorkbookDetectionError,
)


def test_package_exports_semantic_v1_version() -> None:
    assert Version(un_schema_qa.__version__) >= Version("1.0.0")


def test_public_errors_share_toolkit_base() -> None:
    for error_type in (
        ConfigurationError,
        InputFormatError,
        ValidationExecutionError,
        WorkbookDetectionError,
    ):
        assert issubclass(error_type, ToolkitError)
