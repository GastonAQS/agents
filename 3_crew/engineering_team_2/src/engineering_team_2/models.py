from pydantic import BaseModel, Field


class ModuleSpec(BaseModel):
    name: str = Field(description="Module filename, for example backend.py or app.py")
    responsibility: str = Field(description="Main responsibility of the module")
    interfaces: list[str] = Field(
        default_factory=list,
        description="Public classes/functions to expose, including signatures",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Other modules this module depends on",
    )


class ArchitectureSpec(BaseModel):
    app_summary: str = Field(description="One paragraph app summary")
    modules: list[ModuleSpec] = Field(
        default_factory=list,
        description="Complete app module decomposition",
    )
    integration_sequence: list[str] = Field(
        default_factory=list,
        description="Ordered steps for wiring modules together",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Testable requirements for completion",
    )


class TestCaseSpec(BaseModel):
    name: str = Field(description="Test case name")
    objective: str = Field(description="What behavior the test validates")
    inputs: list[str] = Field(
        default_factory=list,
        description="Inputs or setup conditions",
    )
    expected: str = Field(description="Expected outcome")


class QATestStrategy(BaseModel):
    critical_path: str = Field(description="Core end-to-end user flow to validate")
    edge_cases: list[str] = Field(
        default_factory=list,
        description="Edge case scenarios that must be covered",
    )
    test_cases: list[TestCaseSpec] = Field(
        default_factory=list,
        description="Concrete test cases for implementation",
    )
