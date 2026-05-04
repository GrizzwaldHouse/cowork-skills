---
name: visual-test-runner
description: >
  PyQt6 visual test runner that displays real-time test execution with live progress bars,
  pass/fail indicators, console output, and per-test timing. Integrated with the
  self-improving feedback pipeline to provide recurring visual verification of all
  pipeline modules.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Visual Test Runner

> Real-time visual test execution interface for the ClaudeSkills self-improving feedback pipeline. Provides live progress tracking, pass/fail indicators, console output, and per-test timing across 112+ pipeline tests.

## When to Use

- After implementing changes to any pipeline module (scoring, feedback, agent coordination)
- Before committing code to verify no regressions were introduced
- During feedback loop cycles to validate system health
- When debugging test failures and need visual insight into execution flow
- As part of the recurring quality gate (Wave 5 verification)

## Quick Start

Launch the visual test runner standalone:

```bash
cd C:/ClaudeSkills/scripts
py -m gui.test_runner_window
```

The window will open with all 112+ tests queued and ready to run. Use the execution controls to run all tests, selected tests, or tests by category.

## Test Categories

The visual test runner executes tests across 7 test files covering the entire self-improving pipeline:

### Scoring Tests (38 tests)

**test_reusability_scorer.py (13 tests)**
- Validates reusability scoring logic for skill templates
- Checks detection of hardcoded values, magic numbers, configuration-driven design
- Ensures proper scoring of parameterization and generalization patterns

**test_completeness_scorer.py (11 tests)**
- Validates completeness scoring for skill documentation
- Checks presence of required sections (description, usage, examples, configuration)
- Ensures proper scoring of code samples, prerequisites, and error handling guidance

**test_specificity_scorer.py (14 tests)**
- Validates specificity scoring for actionable content
- Checks for vague language, concrete examples, measurable outcomes
- Ensures proper scoring of step-by-step instructions and technical precision

### Feedback Loop Tests (12 tests)

**test_feedback_loop.py (12 tests)**
- Validates feedback loop orchestration and cycle management
- Checks trend analysis (pass rate tracking, performance monitoring)
- Ensures pattern detection (recurring failures, improvement opportunities)
- Validates persistence of feedback data and historical analysis

### Agent Coordination Tests (62 tests)

**test_agent_coordinator.py (30 tests)**
- Validates agent coordination and workflow orchestration
- Checks agent lifecycle management (spawning, monitoring, termination)
- Ensures proper task delegation and result aggregation
- Validates inter-agent communication and state synchronization

**test_extractor_agent.py (20 tests)**
- Validates skill content extraction from SKILL.md files
- Checks parsing of frontmatter, sections, code blocks
- Ensures proper extraction of configuration, examples, and metadata
- Validates handling of malformed or incomplete skill definitions

**test_validator_agent.py (12 tests)**
- Validates skill validation logic and quality checks
- Checks enforcement of coding standards and architectural patterns
- Ensures proper detection of anti-patterns and violations
- Validates output of actionable improvement recommendations

## Integration with Feedback Pipeline

The visual test runner is a critical component of the self-improving feedback loop:

### Pipeline Integration Points

1. **Pre-Cycle Verification**: Run all tests before starting a feedback cycle to establish baseline health
2. **Post-Change Validation**: Run relevant test categories after module modifications
3. **Post-Cycle Quality Gate**: Run all tests after cycle completion to verify no regressions
4. **Health Monitoring**: The feedback_loop.py tracks test pass rates as a system health metric

### Test-Driven Improvement Workflow

```
1. Feedback loop identifies improvement opportunity
2. Agent makes changes to pipeline module
3. Visual test runner executes relevant test category
4. Results inform next cycle:
   - All tests pass: Accept changes, continue to next improvement
   - Tests fail: Investigate root cause, implement fix, re-run tests
```

### Recurring Quality Protocol

The visual test runner enforces a recurring quality gate:

- Run after EVERY module change (scoring logic, agent coordination, feedback analysis)
- Run before git commits (pre-commit verification)
- Run after feedback loop completes a cycle (post-cycle validation)
- Include in Wave 5 quality gate (comprehensive system verification)

## Execution Modes

### Run All Tests

Executes all 112+ pipeline tests sequentially. Use this mode for:
- Pre-commit verification (comprehensive quality gate)
- Post-cycle validation (feedback loop completion)
- Full system health check

**Usage:**
1. Click "Run All Tests" button
2. Monitor progress bar and live test status updates
3. Review summary when complete (Pass/Fail/Error counts)

### Run Selected Tests

Execute specific tests via checkbox selection. Use this mode for:
- Targeted debugging of specific failures
- Validating fixes to specific modules
- Quick iteration during development

**Usage:**
1. Use checkboxes to select tests to run
2. Click "Run Selected Tests" button
3. Only checked tests will execute

### Run by Category

Execute all tests in a specific category. Use this mode for:
- Validating changes to scoring logic (run all scoring tests)
- Validating changes to agent coordination (run all agent tests)
- Validating changes to feedback loop (run feedback tests)

**Categories:**
- Scoring Tests: reusability_scorer, completeness_scorer, specificity_scorer
- Feedback Tests: feedback_loop
- Agent Tests: agent_coordinator, extractor_agent, validator_agent

**Usage:**
1. Expand category group in test tree
2. Check category header to select all tests in category
3. Click "Run Selected Tests" button

## Reading the Results

### Test Status Colors

- **Green**: PASSED - Test executed successfully with all assertions passing
- **Red**: FAILED - Test failed with assertion error or unexpected behavior
- **Orange**: RUNNING - Test is currently executing
- **Purple**: SKIPPED - Test was skipped (pytest skip marker)
- **Gray**: QUEUED - Test has not started yet

### Console Output

The console output panel shows:
- Test execution sequence (which tests are running)
- Stdout/stderr from test execution
- Assertion error messages for failed tests
- Traceback information for debugging failures

### Progress Indicators

**Test Progress Bar**: Shows individual test completion (fills as test runs)

**Overall Progress Bar**: Shows total execution progress (X/Y tests complete)

**Summary Bar**: Shows final counts when execution completes
- Pass: Number of tests that passed
- Fail: Number of tests that failed
- Error: Number of tests with errors (crashes, exceptions)
- Skip: Number of tests skipped

### Per-Test Timing

Each test row displays:
- Test name and module
- Execution status (PASS/FAIL/RUNNING/etc.)
- Execution time in milliseconds (shown after completion)

Use timing data to identify:
- Performance regressions (tests taking longer than baseline)
- Bottlenecks in pipeline execution
- Opportunities for optimization

## Recurring Test Protocol

To maintain pipeline health and prevent regressions, follow this recurring test protocol:

### After Module Changes

1. Identify which pipeline module was modified (scoring, feedback, agent)
2. Launch visual test runner
3. Run tests for the affected category
4. If all tests pass: changes are safe, proceed
5. If tests fail: investigate, fix, re-run until passing

### Before Git Commits

1. Launch visual test runner
2. Run all tests (comprehensive verification)
3. Review console output for any warnings or deprecations
4. Only commit if all tests pass
5. Include test results summary in commit description if relevant

### After Feedback Loop Cycles

1. Feedback loop completes a cycle of improvements
2. Launch visual test runner
3. Run all tests (verify no regressions from improvements)
4. Log test results to feedback_loop.py for trend analysis
5. Use pass rate trends to guide next cycle priorities

### Wave 5 Quality Gate

The visual test runner is the primary tool for Wave 5 verification:

1. All previous waves complete (extraction, scoring, feedback, coordination)
2. Launch visual test runner
3. Run all tests with fresh pytest cache
4. Review detailed console output for any anomalies
5. Verify 100% pass rate before marking system as production-ready
6. Document any skipped tests with justification

## Commands

Run visual test runner:
```bash
cd C:/ClaudeSkills/scripts
py -m gui.test_runner_window
```

Run tests from CLI (for automation):
```bash
cd C:/ClaudeSkills
pytest tests/test_reusability_scorer.py -v
pytest tests/test_completeness_scorer.py -v
pytest tests/test_specificity_scorer.py -v
pytest tests/test_feedback_loop.py -v
pytest tests/test_agent_coordinator.py -v
pytest tests/test_extractor_agent.py -v
pytest tests/test_validator_agent.py -v
```

Run all pipeline tests:
```bash
cd C:/ClaudeSkills
pytest tests/ -v --tb=short
```

Run tests with coverage:
```bash
cd C:/ClaudeSkills
pytest tests/ --cov=scripts --cov-report=html
```

## Test Registry (112+ Tests)

| Test File | Count | Category | Coverage |
|-----------|-------|----------|----------|
| test_reusability_scorer.py | 13 | Scoring | Reusability analysis, hardcoded value detection, parameterization |
| test_completeness_scorer.py | 11 | Scoring | Documentation completeness, required sections, code samples |
| test_specificity_scorer.py | 14 | Scoring | Actionable content, vague language detection, measurable outcomes |
| test_feedback_loop.py | 12 | Feedback | Trend analysis, pattern detection, persistence, health monitoring |
| test_agent_coordinator.py | 30 | Agent | Coordination, lifecycle management, task delegation, state sync |
| test_extractor_agent.py | 20 | Agent | Content extraction, parsing, metadata handling, error recovery |
| test_validator_agent.py | 12 | Agent | Quality checks, standards enforcement, anti-pattern detection |

## Success Criteria

A successful test run requires:
- All tests execute without crashes or hangs
- Pass rate >= 95% (allowing for intentional skips)
- No new test failures compared to baseline
- Console output contains no ERROR-level messages
- Execution time within 20% of baseline (performance regression check)
- All critical path tests passing (agent coordination, feedback loop core)

## Failure Policy

When tests fail:

1. **Immediate Investigation Required**: Failed tests block commits and pipeline cycles
2. **Root Cause Analysis**: Review console output, traceback, and recent code changes
3. **Fix and Re-Run**: Implement fix, run affected test category to verify
4. **Regression Check**: Run full test suite to ensure fix didn't break other tests
5. **Documentation**: Document significant failures in Problem Tracker format

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| test_directory | C:/ClaudeSkills/tests | Directory containing test files |
| pytest_args | -v --tb=short | Default pytest arguments |
| auto_scroll | true | Auto-scroll console to latest output |
| show_timing | true | Display per-test execution time |
| theme | dark | UI theme (dark/light) |
| max_console_lines | 1000 | Maximum console output lines to retain |

## Architecture

### UI Components

**TestRunnerWindow**: Main window with test tree, progress bars, controls
- Inherits from QMainWindow
- Uses QTreeWidget for hierarchical test display
- QProgressBar for overall and per-test progress
- QTextEdit for console output display

**TestTreeItem**: Custom QTreeWidgetItem representing a test
- Stores test metadata (name, module, status, timing)
- Updates visual state based on test status
- Emits signals on state changes

**TestExecutor**: Pytest execution manager (runs in QThread)
- Spawns pytest as subprocess with real-time output capture
- Parses pytest output for test results
- Emits signals for test start, pass, fail, complete

### Signal Flow

```
User clicks "Run All"
  -> TestRunnerWindow.on_run_all_clicked()
  -> TestExecutor.start() [in QThread]
  -> pytest subprocess spawned
  -> TestExecutor.parse_output() [real-time]
  -> Signals emitted: test_started, test_passed, test_failed
  -> TestRunnerWindow slots update UI
  -> Test completes -> summary_ready signal
  -> TestRunnerWindow displays final summary
```

### Event-Driven Design

The visual test runner follows Marcus's universal coding standards:
- All UI updates driven by signals/slots (Observer pattern, NO polling)
- Restrictive access control (private attributes, controlled mutation)
- All defaults set in __init__ (no magic numbers/strings)
- Thread-safe communication (pytest runs in QThread, UI updates on main thread)

## File Structure

```
visual-test-runner/
  SKILL.md                    # This skill definition
  README.md                   # Quick-start guide
  screenshots/
    test_runner_passing.png   # Screenshot of all tests passing
    test_runner_failing.png   # Screenshot with failures highlighted
```

## Best Practices

### Before Running Tests

- Ensure no other pytest processes are running (can cause lock conflicts)
- Clear pytest cache if behavior seems inconsistent: `pytest --cache-clear`
- Ensure test database and fixtures are in clean state

### During Test Execution

- Do NOT close the window while tests are running (pytest subprocess will be orphaned)
- Monitor console output for warnings (may indicate future failures)
- Note any unusually slow tests for performance investigation

### After Test Execution

- Review all failures immediately (don't accumulate technical debt)
- Export console output if needed for debugging: copy from console panel
- Clear console before next run: "Clear Console" button

### Interpreting Failures

**Assertion Errors**: Expected behavior mismatch, likely code regression
**Import Errors**: Missing dependencies or module path issues
**Fixture Errors**: Test setup failure, check fixture definitions
**Timeout Errors**: Test hanging, likely infinite loop or deadlock

## Platform Notes

### Windows
- Pytest subprocess spawned with `CREATE_NO_WINDOW` flag (no console popup)
- Console output uses ANSI color codes (parsed and styled in UI)
- File paths use forward slashes (C:/ClaudeSkills/tests)

### Cross-Platform Considerations
- QThread for subprocess management (cross-platform threading)
- Path handling via pathlib (platform-agnostic)
- ANSI escape code parsing (works on all platforms with colorama fallback)

## Testing the Test Runner

The visual test runner itself should be tested:

```python
# test_test_runner.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for visual test runner window

def test_window_opens(qtbot):
    """Test that test runner window opens without errors."""
    from scripts.gui.test_runner_window import TestRunnerWindow
    window = TestRunnerWindow()
    qtbot.addWidget(window)
    assert window.isVisible()

def test_all_tests_loaded(qtbot):
    """Test that all 112+ tests are loaded into tree."""
    from scripts.gui.test_runner_window import TestRunnerWindow
    window = TestRunnerWindow()
    qtbot.addWidget(window)

    # Count test items in tree
    test_count = count_test_items(window.test_tree)
    assert test_count >= 112

def test_run_all_executes(qtbot):
    """Test that Run All button triggers test execution."""
    from scripts.gui.test_runner_window import TestRunnerWindow
    window = TestRunnerWindow()
    qtbot.addWidget(window)

    # Connect to signal
    with qtbot.waitSignal(window.execution_started, timeout=5000):
        window.on_run_all_clicked()
```

## Integration with Other Skills

- **PyQt6 UI Debugger**: Use to debug visual test runner UI issues
- **Python Code Reviewer**: Review test code for quality and adherence to standards
- **Desktop UI Designer**: Design patterns used in test runner window
- **Universal Coding Standards**: Event-driven communication, access control, initialization
- **Dev Workflow**: Brainstorm-first methodology, recurring quality gates

## Notes

- **Real-time output**: Console updates during test execution, not just at end
- **Thread safety**: Pytest runs in background thread, UI updates marshalled to main thread via signals
- **Performance**: 112+ tests complete in ~30-60 seconds (depends on system)
- **Memory usage**: Console output limited to 1000 lines to prevent memory bloat
- **Crash recovery**: If pytest crashes, window remains responsive and shows error state
- **Multiple runs**: Can re-run tests without restarting window
- **Selective execution**: Checkbox selection allows running subset of tests
- **Category filtering**: Group tests by module for targeted execution

## Future Enhancements

Potential improvements to the visual test runner:

1. **Parallel Execution**: Run tests in parallel using pytest-xdist
2. **Historical Trends**: Graph pass rate over time
3. **Failure Clustering**: Group failures by root cause
4. **Performance Profiling**: Flame graph of test execution time
5. **Auto-Retry**: Automatically retry flaky tests
6. **Test Generation**: Generate missing tests based on coverage gaps
7. **Export Reports**: Export test results to HTML/JSON/XML
8. **Integration with CI/CD**: Trigger test runs from GitHub Actions

## Further Reading

- pytest Documentation: https://docs.pytest.org/
- PyQt6 QThread: https://doc.qt.io/qt-6/qthread.html
- ClaudeSkills Feedback Loop: See `scripts/feedback_loop.py`
- Agent Coordination: See `scripts/agent_coordinator.py`
- Scoring Modules: See `scripts/reusability_scorer.py`, `completeness_scorer.py`, `specificity_scorer.py`
