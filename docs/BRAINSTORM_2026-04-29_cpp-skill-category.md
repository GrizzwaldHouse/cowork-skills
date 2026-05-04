# C++ SKILL CATEGORY BRAINSTORM RESPONSES
Captured: 2026-04-29

This artifact validates the brainstorm-artifact skill end-to-end by exercising
its full output specification on a real next-step decision: how to add a C++
category to the skills taxonomy now that the modular structure is in place.

Mark choices by changing `[ ]` to `[x]`. Strike through unwanted options. Add
new options where the existing set falls short.

## CATEGORY PLACEMENT AND SCOPE

Where does the C++ category sit in the new taxonomy?
[ ] Under software-dev/cpp/: Treats general C++ as a sibling of python and web, separate from game-dev/ue5 which already covers engine-specific C++.
[ ] Split between software-dev/cpp/ and game-dev/ue5/: Two homes by intent, with cross-references between skills that span both.
[ ] Single top-level cpp/: Promotes C++ to a peer of game-dev and software-dev because it underlies both, at the cost of breaking the discipline-first rule.

What scope of C++ practice should the first wave of skills cover?
[ ] Modern C++ (17/20/23) idioms only: Constrains to current-portfolio practice, leaves legacy code patterns out.
[ ] Modern C++ plus C++14 maintenance patterns: Wider net for older codebases, more surface to maintain.
[ ] Modern C++ plus engine integration (UE5, Unity native plugins): Aligns with Marcus's portfolio focus, narrows away from pure systems C++.

Which existing skills graduate first into the C++ category?
[ ] universal-coding-standards C++ subset: Extract the C++-specific rules from _core/universal-coding-standards into a dedicated cpp-coding-standards skill.
[ ] ue5-blueprint-organization companion: Add a cpp-ue5-architecture skill focused on Actor Component vs Subsystem decisions.
[ ] None yet, scaffold empty: Reserve the folder, defer skills until a real project demands one.

## CRITICAL SKILL CANDIDATES

Which build-and-tooling skill belongs here first?
[ ] cpp-cmake-conventions: Cross-platform CMake patterns Marcus can reuse from project to project (the 95/5 rule applied to build).
[ ] cpp-msvc-clang-toolchain: Compiler-specific flags, sanitizers, and warning baselines for both stacks.
[ ] cpp-package-management: vcpkg/Conan wiring with lockfile policy and reproducibility guarantees.

Which code-review skill belongs here first?
[ ] cpp-code-reviewer (sibling of python-code-reviewer): Review against the universal-coding-standards plus C++-specific rules (rule of zero/three/five, RAII, no raw owning pointers).
[ ] cpp-undefined-behavior-auditor: Targets UB hotspots (signed overflow, lifetime, aliasing) using sanitizer-driven evidence rather than style.
[ ] cpp-perf-reviewer: Cache lines, false sharing, allocator behavior, branch prediction notes.

Which testing skill belongs here first?
[ ] cpp-gtest-strategy: GoogleTest patterns for unit, fixture, and parameterized tests aligned with the testing-strategy skill.
[ ] cpp-doctest-strategy: doctest preference for header-only, self-contained tests that compile fast.
[ ] cpp-fuzz-and-property: libFuzzer plus rapidcheck for inputs that exercise the system beyond hand-written cases.

## CROSS-CUTTING CONCERNS

How should Unreal-specific C++ relate to general C++ skills?
[ ] Unreal skills under game-dev/ue5/, general C++ under software-dev/cpp/: Discipline boundary stays clean, with cross-reference links inside each SKILL.md.
[ ] Shared cpp-foundations skill in _core/: Pull C++ idioms common to both into _core so neither category duplicates them.
[ ] Mirror folders in both categories: Duplicate ergonomic content in both places to avoid cross-tree navigation. Increases maintenance cost.

How does the publish guard treat C++ project codenames going forward?
[ ] Add codenames to config/publish_guard.json as they appear: Keeps detection explicit, requires discipline to update.
[ ] Auto-extract codenames from new SKILL.md files: Convenient, but introduces hidden state and risks false negatives on drift.
[ ] Maintain a cpp-codenames separate config block: Allows scoped rules per language, increases config surface.

What does the skill_creator workflow generate for a new C++ skill?
[ ] Same template as Python skills, with C++-flavored examples: Maximum reuse, minimum special casing.
[ ] C++-specific template under skill_creator/templates/cpp/: Better fit for header-and-source examples and CMake snippets.
[ ] Hybrid: shared template, optional cpp-extras section appended automatically: Best of both, more logic in skill_creator.

## VALIDATION AND ROLLOUT

How is the new category validated before merging?
[ ] cowork_setup_orchestrator dry-run shows the new category appears in the walk: Smoke test that the recursive installer picked it up.
[ ] publish_guard audit mode passes with the new codenames added: Confirms IP posture remains intact.
[ ] Headless install verifies marker skills land in ~/.claude/skills: End-to-end install proof.

What is the rollout cadence for the first three C++ skills?
[ ] One skill per week, each with its own brainstorm artifact: Steady cadence aligned with Marcus's quality-over-speed rule.
[ ] Three skills in one batch after a single combined brainstorm: Faster, but combines unrelated concerns into one decision pass.
[ ] One skill, evaluated for two sessions, then expand: Slowest, gives the most signal on whether the category shape works.

## OUTCOME RECORD

This artifact's role inside the skills repo:
[ ] Lock at docs/BRAINSTORM_2026-04-29_cpp-skill-category.md after Marcus marks his choices.
[ ] Reference the locked file from CLAUDE.md under a "Locked brainstorms" list so future sessions resume without re-litigating.
[ ] Treat as discardable demo only and remove after the skill test confirms format.

Notes on this run:

The skill was invoked from ~/.claude/skills/brainstorm-artifact, installed there
by the cowork_setup_orchestrator on 2026-04-29 from the source path
C:\ClaudeSkills\skills\_core\brainstorm-artifact. The .source marker file in
the install target confirms the recursive walker picked the right manifest.
The artifact above follows the section-question-options format described in
the skill's SKILL.md (lines 30 to 100), respects the trade-off-per-line rule,
and avoids the anti-patterns called out in the skill's own document.
