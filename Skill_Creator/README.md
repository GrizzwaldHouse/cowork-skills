# Skill Creator

The Skill Creator is a meta-skill that provides the template and conventions for building new Claude Skills.

## Purpose

When you want to add a new skill to the Claude Skills system, start here. The `SKILL.md` file in this folder is the canonical template -- copy it into a new skill folder and fill in each section.

## How to Create a New Skill

1. **Create a folder** under `Example_Skills/` (or another appropriate location) with a descriptive kebab-case name.
   ```
   Example_Skills/my-new-skill/
   ```
2. **Copy the template** from this folder:
   ```
   cp Skill_Creator/SKILL.md Example_Skills/my-new-skill/SKILL.md
   ```
3. **Fill in every section** of the copied `SKILL.md` -- Name, Description, Prerequisites, Usage, Examples, and Configuration.
4. **Add a README.md** that gives a quick overview and getting-started instructions.
5. **Create a `resources/` subfolder** if your skill needs supporting files (prompt snippets, config templates, reference data).
6. **Register the skill** in `cloud/main_cloud.json` so it can be discovered and synced.

## Conventions

- Use **relative paths** in all documentation so skills are portable.
- Keep skill names in **kebab-case** (lowercase, hyphens between words).
- One skill per folder. Each folder must contain at least `SKILL.md` and `README.md`.
