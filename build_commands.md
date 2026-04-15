# Build Commands Reference

Quick reference for clean build + validation commands per language/framework.
Used by Phase 5 (Validation and Build) of the recovery pipeline.

## C++ / Unreal Engine 5.4
```bash
# IMPORTANT: Close Unreal Editor before building in Visual Studio
# Live Coding conflicts with full VS builds

# Visual Studio build (preferred)
# Use Build > Rebuild Solution (not just Build)

# Command-line build via UnrealBuildTool
Engine/Build/BatchFiles/Build.bat <ProjectName>Editor Win64 Development

# Check for warnings — UE5 generates many; focus on YOUR module
# Filter by your module name in the output
```

## C# / .NET
```bash
# Clean + rebuild (catches stale artifacts)
dotnet clean && dotnet build --no-incremental

# With warnings as errors (strict mode)
dotnet build -warnaserror

# Run with logging
dotnet run 2>&1 | tee build_output.log
```

## Python
```bash
# Syntax check all files
python -m py_compile *.py

# Type checking (catches type errors statically)
mypy . --strict
# or
pyright .

# Import validation (catches circular imports)
python -c "import your_module"

# Full lint
ruff check .
# or
flake8 .
```

## TypeScript / Node.js
```bash
# Type check without emitting
npx tsc --noEmit

# Full build
npm run build

# Lint
npx eslint . --ext .ts,.tsx

# Check for unused imports
npx ts-unused-exports tsconfig.json
```

## Rust
```bash
# Build
cargo build

# Build with all warnings
cargo build 2>&1

# Lint (catches common mistakes)
cargo clippy -- -D warnings

# Format check
cargo fmt -- --check
```

## Java
```bash
# Maven
mvn clean compile

# Gradle  
gradle clean build

# With strict warnings
javac -Xlint:all -Werror *.java
```

## Go
```bash
# Build
go build ./...

# Vet (catches suspicious constructs)
go vet ./...

# Lint
golangci-lint run
```

## Universal Post-Build Checks
After a clean build, always verify:
1. Zero errors in build output
2. Zero warnings (or justified suppressions)
3. Application launches without crash
4. Core functionality works (manual smoke test)
5. No error-level entries in application logs
