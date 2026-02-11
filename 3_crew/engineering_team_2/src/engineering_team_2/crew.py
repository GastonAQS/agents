import ast
import importlib.util
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from crewai import Agent, Crew, Process, Task, TaskOutput
from crewai.project import CrewBase, agent, before_kickoff, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from engineering_team_2.models import ArchitectureSpec
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class EngineeringTeam2:
    """EngineeringTeam2 crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
    _kickoff_inputs: Dict[str, Any]
    _repair_attempted: bool = False
    _repair_in_progress: bool = False

    @before_kickoff
    def setup_guardrails(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Store kickoff inputs so callbacks can run controlled recovery flows.
        self._kickoff_inputs = inputs
        self._repair_attempted = False
        self._repair_in_progress = False
        return inputs

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def architect(self) -> Agent:
        return Agent(
            config=self.agents_config["architect"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_engineer"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def integration_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["integration_engineer"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def qa_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["qa_engineer"],  # type: ignore[index]
            verbose=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def architecture_task(self) -> Task:
        return Task(
            config=self.tasks_config["architecture_task"],  # type: ignore[index]
            output_pydantic=ArchitectureSpec,
        )

    @task
    def backend_task(self) -> Task:
        return Task(
            config=self.tasks_config["backend_task"],  # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config["frontend_task"],  # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
        )

    @task
    def integration_task(self) -> Task:
        return Task(
            config=self.tasks_config["integration_task"],  # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
            callback=self.on_integration_done,
        )

    @task
    def qa_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["qa_strategy_task"],  # type: ignore[index]
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config["test_task"],  # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
        )

    def _smoke_check_artifacts(self) -> list[str]:
        errors: list[str] = []
        output_dir = Path("output")
        module_name = str(self._kickoff_inputs.get("module_name", "backend.py"))
        module_file = Path(module_name)
        backend_module_filename = module_file.name
        backend_import_name = module_file.stem
        required_files = [
            output_dir / backend_module_filename,
            output_dir / "app.py",
            output_dir / "main.py",
        ]

        for file_path in required_files:
            if not file_path.exists():
                errors.append(f"Missing required artifact: {file_path}")
                continue
            try:
                py_compile.compile(str(file_path), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"Syntax error in {file_path}: {exc.msg}")

        # Import/runtime wiring probe (catches broken imports and missing symbols).
        if not errors:
            import_probe = (
                "import sys\n"
                "from pathlib import Path\n"
                "sys.path.insert(0, str(Path('output').resolve()))\n"
                f"import {backend_import_name}\n"
                "import main\n"
            )
            result = subprocess.run(
                [sys.executable, "-c", import_probe],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                details = stderr if stderr else stdout
                errors.append(
                    f"Import smoke check failed for output modules: {details}"
                )
            else:
                errors.extend(
                    self._validate_backend_symbol_contract(
                        backend_module_filename=backend_module_filename,
                        backend_import_name=backend_import_name,
                        consumer_files=[output_dir / "app.py", output_dir / "main.py"],
                    )
                )

        return errors

    def _validate_backend_symbol_contract(
        self,
        backend_module_filename: str,
        backend_import_name: str,
        consumer_files: list[Path],
    ) -> list[str]:
        contract_errors: list[str] = []
        output_dir = Path("output")
        backend_path = output_dir / backend_module_filename

        required_symbols: set[str] = set()
        for consumer_file in consumer_files:
            if not consumer_file.exists():
                continue
            try:
                parsed = ast.parse(consumer_file.read_text(encoding="utf-8"))
            except Exception as exc:
                contract_errors.append(f"Unable to parse {consumer_file}: {exc}")
                continue

            for node in ast.walk(parsed):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module == backend_import_name
                ):
                    for alias in node.names:
                        if alias.name != "*":
                            required_symbols.add(alias.name)

        if not required_symbols:
            return contract_errors

        spec = importlib.util.spec_from_file_location(backend_import_name, backend_path)
        if spec is None or spec.loader is None:
            contract_errors.append(
                f"Unable to load backend module for contract check: {backend_path}"
            )
            return contract_errors

        backend_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(backend_module)
        except Exception as exc:
            contract_errors.append(
                f"Backend module failed to load for contract check: {exc}"
            )
            return contract_errors

        missing = sorted(
            symbol for symbol in required_symbols if not hasattr(backend_module, symbol)
        )
        if missing:
            contract_errors.append(
                "Backend import contract mismatch. Missing exported symbols: "
                + ", ".join(missing)
            )

        return contract_errors

    @staticmethod
    def _escape_template_tokens(text: str) -> str:
        # CrewAI interpolates `{var}` patterns in task descriptions.
        # Escape braces in dynamic callback content to prevent accidental template lookups.
        return text.replace("{", "{{").replace("}", "}}")

    def _run_repair_flow(
        self, smoke_errors: list[str], integration_output: str
    ) -> None:
        module_name = str(self._kickoff_inputs.get("module_name", "backend.py"))
        backend_module_filename = Path(module_name).name
        requirements = str(self._kickoff_inputs.get("requirements", ""))
        safe_requirements = self._escape_template_tokens(requirements)
        safe_integration_output = self._escape_template_tokens(integration_output)
        safe_smoke_errors = [self._escape_template_tokens(err) for err in smoke_errors]

        backend_repair_task = Task(
            description=(
                f"Repair the backend module {module_name} so it matches the architecture and integration needs.\n"
                f"Fix issues discovered by smoke checks:\n- "
                + "\n- ".join(safe_smoke_errors)
            ),
            expected_output=(
                f"Valid Python code for {module_name}. "
                "Output ONLY raw Python code without markdown or code fences."
            ),
            agent=self.backend_engineer(),
            output_file=f"output/{module_name}",
        )

        integration_repair_task = Task(
            description=(
                "Repair output/main.py and its wiring with output/app.py and backend module.\n"
                "Use these constraints:\n"
                f"- Requirements: {safe_requirements}\n"
                "- Keep imports and startup flow runnable from output/main.py.\n"
                "Observed integration output:\n"
                f"{safe_integration_output}\n"
                "Smoke-check failures:\n- " + "\n- ".join(safe_smoke_errors)
            ),
            expected_output=(
                "Valid Python code for output/main.py that correctly wires the app. "
                "Output ONLY raw Python code without markdown or code fences."
            ),
            agent=self.integration_engineer(),
            context=[backend_repair_task],
            output_file="output/main.py",
        )

        repair_crew = Crew(
            agents=[self.backend_engineer(), self.integration_engineer()],
            tasks=[backend_repair_task, integration_repair_task],
            process=Process.sequential,
            verbose=True,
        )
        # Guardrail: pass only minimal scalar inputs to avoid interpolation failures
        # from arbitrary payload keys/values in the parent kickoff.
        repair_inputs = {
            "requirements": safe_requirements,
            "module_name": backend_module_filename,
        }
        try:
            repair_crew.kickoff(inputs=repair_inputs)
        except ValueError as exc:
            # Last-resort fallback: run without interpolation inputs if repair tasks
            # do not depend on templates.
            print(f"[Guardrail] Repair kickoff interpolation failed: {exc}")
            print("[Guardrail] Retrying repair kickoff without inputs.")
            repair_crew.kickoff()

    def on_integration_done(self, output: TaskOutput) -> None:
        # Guardrail 1: avoid recursive callback loops.
        if self._repair_in_progress:
            return

        smoke_errors = self._smoke_check_artifacts()
        if not smoke_errors:
            return

        # Guardrail 2: single automated repair attempt per kickoff.
        if self._repair_attempted:
            print(
                "[Guardrail] Integration smoke check failed after repair attempt; "
                "skipping further automatic retries."
            )
            for err in smoke_errors:
                print(f"[Guardrail] {err}")
            return

        self._repair_attempted = True
        self._repair_in_progress = True
        try:
            print(
                "[Callback] Integration smoke check failed. Running one automated repair flow."
            )
            try:
                self._run_repair_flow(
                    smoke_errors=smoke_errors, integration_output=output.raw or ""
                )
                post_repair_errors = self._smoke_check_artifacts()
                if post_repair_errors:
                    print(
                        "[Guardrail] Repair flow completed but smoke check still fails:"
                    )
                    for err in post_repair_errors:
                        print(f"[Guardrail] {err}")
            except Exception as exc:
                # Guardrail 3: callback must not fail the parent task execution.
                print(f"[Guardrail] Repair callback failed and was suppressed: {exc}")
        finally:
            self._repair_in_progress = False

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam2 crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
