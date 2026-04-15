# detect_interruption.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Automated detection of where an AI agent session was interrupted.
#          Scans git history, filesystem timestamps, code markers, and build
#          state to produce a recovery_anchor identifying the exact point of
#          interruption. Designed for cross-language, cross-framework use.

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# Marker patterns that indicate incomplete code across languages
INCOMPLETE_MARKERS = [
    r'\bTODO\b', r'\bFIXME\b', r'\bHACK\b', r'\bXXX\b',
    r'\bINCOMPLETE\b', r'\bWIP\b', r'\bTEMP\b',
    r'\bNotImplementedException\b', r'\bNotImplementedError\b',
    r'\bunimplemented!\b', r'\btodo!\b',
    r'\bpass\s*$',  # Python placeholder
    r'\bthrow\s+new\s+NotImplementedException',  # C#
    r'\braise\s+NotImplementedError',  # Python
]

# Patterns for empty function bodies per language
EMPTY_BODY_PATTERNS = {
    'cpp':    r'(?:void|int|float|bool|auto|FString|TArray)\s+\w+\s*\([^)]*\)\s*\{\s*\}',
    'csharp': r'(?:void|int|string|bool|Task|async)\s+\w+\s*\([^)]*\)\s*\{\s*\}',
    'python': r'def\s+\w+\s*\([^)]*\)\s*:\s*\n\s*pass',
    'typescript': r'(?:function|async\s+function|const\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)\s*\{\s*\}',
    'rust':   r'fn\s+\w+\s*\([^)]*\)\s*(?:->\s*\w+)?\s*\{\s*\}',
}

# File extensions per language family
LANGUAGE_MAP = {
    '.cpp': 'cpp', '.h': 'cpp', '.hpp': 'cpp', '.cc': 'cpp',
    '.cs': 'csharp',
    '.py': 'python',
    '.ts': 'typescript', '.tsx': 'typescript', '.js': 'typescript', '.jsx': 'typescript',
    '.rs': 'rust',
    '.java': 'java',
    '.go': 'go',
}

# Directories to skip during scanning
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'Binaries', 'Intermediate',
    'Saved', 'DerivedDataCache', '.vs', 'dist', 'build', 'target',
    '.next', 'coverage', 'venv', '.venv', 'env',
}


@dataclass
class IncompleteCode:
    """Represents a detected piece of incomplete code."""
    file_path: str
    line_number: int
    marker_type: str
    context: str
    modified_time: float
    
    
@dataclass
class RecoveryAnchor:
    """The primary output — identifies exactly where work was interrupted."""
    file: str
    function: str
    line: int
    state: str  # EMPTY_BODY | PARTIAL_IMPL | COMMENTS_ONLY | BUILD_ERROR
    context: str
    modified: str
    git_hash: str
    git_message: str
    incomplete_items: list = field(default_factory=list)
    confidence: float = 0.0


def run_git_command(cmd: str, project_root: str) -> Optional[str]:
    """Execute a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd.split(), capture_output=True, text=True,
            cwd=project_root, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def scan_git_state(project_root: str) -> dict:
    """Gather git history and uncommitted change information."""
    state = {
        'recent_commits': [],
        'uncommitted_files': [],
        'stashed_work': [],
        'last_commit_hash': '',
        'last_commit_message': '',
    }
    
    # Recent commits
    log_output = run_git_command('git log --oneline -20', project_root)
    if log_output:
        for line in log_output.split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                state['recent_commits'].append({
                    'hash': parts[0],
                    'message': parts[1] if len(parts) > 1 else ''
                })
        if state['recent_commits']:
            state['last_commit_hash'] = state['recent_commits'][0]['hash']
            state['last_commit_message'] = state['recent_commits'][0]['message']
    
    # Uncommitted changes
    diff_output = run_git_command('git diff --name-only', project_root)
    if diff_output:
        state['uncommitted_files'] = [f for f in diff_output.split('\n') if f.strip()]
    
    # Staged but uncommitted
    staged_output = run_git_command('git diff --name-only --cached', project_root)
    if staged_output:
        state['uncommitted_files'].extend(
            [f for f in staged_output.split('\n') if f.strip()]
        )
    
    # Untracked files
    untracked = run_git_command('git ls-files --others --exclude-standard', project_root)
    if untracked:
        state['uncommitted_files'].extend(
            [f for f in untracked.split('\n') if f.strip()]
        )
    
    # Stashed work
    stash_output = run_git_command('git stash list', project_root)
    if stash_output:
        state['stashed_work'] = [s for s in stash_output.split('\n') if s.strip()]
    
    return state


def scan_for_incomplete_code(project_root: str) -> list[IncompleteCode]:
    """Walk the source tree looking for incomplete code markers."""
    findings = []
    root_path = Path(project_root)
    
    for path in root_path.rglob('*'):
        # Skip non-source files and excluded directories
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix not in LANGUAGE_MAP:
            continue
        if not path.is_file():
            continue
            
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            mod_time = path.stat().st_mtime
            
            for i, line in enumerate(lines, 1):
                for pattern in INCOMPLETE_MARKERS:
                    if re.search(pattern, line):
                        # Grab surrounding context (2 lines before, 2 after)
                        start = max(0, i - 3)
                        end = min(len(lines), i + 2)
                        context = '\n'.join(lines[start:end])
                        
                        findings.append(IncompleteCode(
                            file_path=str(path.relative_to(root_path)),
                            line_number=i,
                            marker_type=pattern.replace(r'\b', '').replace('\\', ''),
                            context=context[:200],
                            modified_time=mod_time,
                        ))
                        break  # One finding per line is enough
                        
        except (PermissionError, OSError):
            continue
    
    return findings


def scan_for_empty_bodies(project_root: str) -> list[IncompleteCode]:
    """Find functions with empty bodies (declared but not implemented)."""
    findings = []
    root_path = Path(project_root)
    
    for path in root_path.rglob('*'):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix not in LANGUAGE_MAP:
            continue
        if not path.is_file():
            continue
        
        lang = LANGUAGE_MAP[path.suffix]
        if lang not in EMPTY_BODY_PATTERNS:
            continue
            
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            mod_time = path.stat().st_mtime
            
            for match in re.finditer(EMPTY_BODY_PATTERNS[lang], content):
                # Calculate line number from character position
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(IncompleteCode(
                    file_path=str(path.relative_to(root_path)),
                    line_number=line_num,
                    marker_type='EMPTY_BODY',
                    context=match.group()[:200],
                    modified_time=mod_time,
                ))
                
        except (PermissionError, OSError):
            continue
    
    return findings


def find_comments_without_code(project_root: str) -> list[IncompleteCode]:
    """Find step-comments (CDD pattern) that lack implementation beneath them."""
    findings = []
    root_path = Path(project_root)
    # Matches CDD step comments like "// STEP 1:" or "# STEP 2:"
    step_pattern = re.compile(r'^\s*(?://|#)\s*STEP\s+\d+\s*:', re.IGNORECASE)
    
    for path in root_path.rglob('*'):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix not in LANGUAGE_MAP:
            continue
        if not path.is_file():
            continue
            
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            mod_time = path.stat().st_mtime
            
            for i, line in enumerate(lines):
                if step_pattern.match(line):
                    # Check if the next non-comment, non-empty line has code
                    has_code = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            continue
                        if next_line.startswith('//') or next_line.startswith('#'):
                            continue
                        has_code = True
                        break
                    
                    if not has_code:
                        findings.append(IncompleteCode(
                            file_path=str(path.relative_to(root_path)),
                            line_number=i + 1,
                            marker_type='COMMENTS_ONLY',
                            context=line.strip()[:200],
                            modified_time=mod_time,
                        ))
                        
        except (PermissionError, OSError):
            continue
    
    return findings


def get_recently_modified_files(project_root: str, count: int = 15) -> list[dict]:
    """Get the most recently modified source files."""
    root_path = Path(project_root)
    source_files = []
    
    for path in root_path.rglob('*'):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix not in LANGUAGE_MAP:
            continue
        if not path.is_file():
            continue
            
        try:
            stat = path.stat()
            source_files.append({
                'path': str(path.relative_to(root_path)),
                'modified': stat.st_mtime,
                'modified_human': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'size': stat.st_size,
            })
        except OSError:
            continue
    
    source_files.sort(key=lambda f: f['modified'], reverse=True)
    return source_files[:count]


def determine_recovery_anchor(
    git_state: dict,
    incomplete_markers: list[IncompleteCode],
    empty_bodies: list[IncompleteCode],
    orphan_comments: list[IncompleteCode],
    recent_files: list[dict],
) -> RecoveryAnchor:
    """Cross-reference all signals to determine the most likely interruption point."""
    
    # Combine all findings and score by recency + severity
    all_findings = []
    
    for item in incomplete_markers:
        all_findings.append(('PARTIAL_IMPL', item, 2.0))
    for item in empty_bodies:
        all_findings.append(('EMPTY_BODY', item, 3.0))
    for item in orphan_comments:
        all_findings.append(('COMMENTS_ONLY', item, 4.0))
    
    if not all_findings:
        # No incomplete code found — check git for uncommitted changes
        if git_state['uncommitted_files']:
            return RecoveryAnchor(
                file=git_state['uncommitted_files'][0],
                function='(uncommitted changes detected)',
                line=0,
                state='UNCOMMITTED_CHANGES',
                context=f"Found {len(git_state['uncommitted_files'])} uncommitted file(s)",
                modified=recent_files[0]['modified_human'] if recent_files else 'unknown',
                git_hash=git_state.get('last_commit_hash', 'unknown'),
                git_message=git_state.get('last_commit_message', 'unknown'),
                confidence=0.5,
            )
        
        return RecoveryAnchor(
            file='(none detected)',
            function='(no interruption found)',
            line=0,
            state='CLEAN',
            context='No incomplete code detected. Session may have completed normally.',
            modified=recent_files[0]['modified_human'] if recent_files else 'unknown',
            git_hash=git_state.get('last_commit_hash', 'unknown'),
            git_message=git_state.get('last_commit_message', 'unknown'),
            confidence=0.0,
        )
    
    # Score: higher = more likely the interruption point
    # Boost score for files that are also in the uncommitted git changes
    uncommitted_set = set(git_state.get('uncommitted_files', []))
    recent_set = set(f['path'] for f in recent_files[:5])
    
    scored = []
    for state, item, base_score in all_findings:
        score = base_score
        if item.file_path in uncommitted_set:
            score += 3.0
        if item.file_path in recent_set:
            score += 2.0
        # Recency bonus — more recent = more likely the interruption
        score += item.modified_time / 1e10
        scored.append((score, state, item))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_state, best_item = scored[0]
    
    # Normalize confidence to 0.0 - 1.0
    max_possible = 4.0 + 3.0 + 2.0 + (best_item.modified_time / 1e10)
    confidence = min(best_score / max_possible, 1.0)
    
    return RecoveryAnchor(
        file=best_item.file_path,
        function=best_item.context.split('\n')[0][:80],
        line=best_item.line_number,
        state=best_state,
        context=best_item.context,
        modified=datetime.fromtimestamp(best_item.modified_time).isoformat(),
        git_hash=git_state.get('last_commit_hash', 'unknown'),
        git_message=git_state.get('last_commit_message', 'unknown'),
        incomplete_items=[
            {'file': s[2].file_path, 'line': s[2].line_number, 'type': s[1], 'score': round(s[0], 2)}
            for s in scored[:10]
        ],
        confidence=round(confidence, 3),
    )


def main():
    parser = argparse.ArgumentParser(
        description='Detect where an AI agent session was interrupted'
    )
    parser.add_argument(
        '--project-root', '-p', default='.',
        help='Root directory of the project to scan'
    )
    parser.add_argument(
        '--output', '-o', default=None,
        help='Output file path for JSON report (default: stdout)'
    )
    parser.add_argument(
        '--format', '-f', choices=['json', 'text'], default='text',
        help='Output format (default: text)'
    )
    args = parser.parse_args()
    
    project_root = os.path.abspath(args.project_root)
    
    print(f"[SCAN] Scanning project: {project_root}", file=sys.stderr)
    
    # Phase 1a: Git state
    print("[SCAN] Checking git history...", file=sys.stderr)
    git_state = scan_git_state(project_root)
    
    # Phase 1b: Incomplete code markers
    print("[SCAN] Scanning for incomplete code markers...", file=sys.stderr)
    incomplete = scan_for_incomplete_code(project_root)
    
    # Phase 1c: Empty function bodies
    print("[SCAN] Scanning for empty function bodies...", file=sys.stderr)
    empty = scan_for_empty_bodies(project_root)
    
    # Phase 1d: Orphan step-comments
    print("[SCAN] Scanning for orphan CDD comments...", file=sys.stderr)
    orphans = find_comments_without_code(project_root)
    
    # Phase 1e: Recent files
    print("[SCAN] Analyzing file modification times...", file=sys.stderr)
    recent = get_recently_modified_files(project_root)
    
    # Cross-reference and produce anchor
    anchor = determine_recovery_anchor(git_state, incomplete, empty, orphans, recent)
    
    total_findings = len(incomplete) + len(empty) + len(orphans)
    print(f"[SCAN] Found {total_findings} incomplete code indicators", file=sys.stderr)
    print(f"[SCAN] Recovery anchor confidence: {anchor.confidence}", file=sys.stderr)
    
    # Format output
    if args.format == 'json':
        output = json.dumps({
            'recovery_anchor': asdict(anchor),
            'git_state': git_state,
            'recently_modified': recent,
            'scan_timestamp': datetime.now().isoformat(),
            'total_findings': total_findings,
        }, indent=2, default=str)
    else:
        output = f"""
================================================================================
                        SESSION RECOVERY ANCHOR REPORT
================================================================================
Scan Time:   {datetime.now().isoformat()}
Project:     {project_root}
Confidence:  {anchor.confidence * 100:.1f}%

RECOVERY ANCHOR
===============
File:        {anchor.file}
Function:    {anchor.function}
Line:        {anchor.line}
State:       {anchor.state}
Context:     {anchor.context[:300]}
Modified:    {anchor.modified}
Git Hash:    {anchor.git_hash}
Git Message: {anchor.git_message}

FINDINGS SUMMARY
================
Incomplete markers:   {len(incomplete)}
Empty function bodies: {len(empty)}
Orphan CDD comments:  {len(orphans)}
Uncommitted files:    {len(git_state.get('uncommitted_files', []))}
Stashed work:         {len(git_state.get('stashed_work', []))}

TOP CANDIDATES (ranked by likelihood)
=====================================
"""
        for item in anchor.incomplete_items[:10]:
            output += f"  [{item['score']:5.2f}] {item['type']:15s} {item['file']}:{item['line']}\n"
        
        output += f"""
RECENTLY MODIFIED FILES
=======================
"""
        for f in recent[:10]:
            output += f"  {f['modified_human']}  {f['path']}\n"
    
    if args.output:
        Path(args.output).write_text(output)
        print(f"[DONE] Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
