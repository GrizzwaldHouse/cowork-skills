// SkillBadge.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Small chip component that shows an active skill name.
//          Click expands a popover with the SKILL.md summary fetched
//          from GET /projects/{id}/skills/{slug} (future endpoint).
//          Used in PhaseCard and the ProjectSwitcher sidebar.

import { useState } from 'react';

interface SkillBadgeProps {
  readonly slug: string;
  readonly onClick?: (slug: string) => void;
}

export function SkillBadge({ slug, onClick }: SkillBadgeProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onClick={() => onClick?.(slug)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      title={`Skill: ${slug}`}
      style={{
        background: hovered
          ? 'rgba(120,140,255,0.22)'
          : 'rgba(100,120,255,0.10)',
        border: '1px solid rgba(100,120,255,0.30)',
        borderRadius: 4,
        padding: '3px 9px',
        fontSize: 11,
        color: hovered ? 'rgba(200,215,255,0.95)' : 'rgba(160,180,255,0.75)',
        cursor: onClick ? 'pointer' : 'default',
        fontFamily: 'inherit',
        transition: 'all 0.12s',
        letterSpacing: '0.04em',
      }}
    >
      {slug}
    </button>
  );
}

// ---------------------------------------------------------------------------
// SkillBadgeList — renders multiple badges in a flex row
// ---------------------------------------------------------------------------

interface SkillBadgeListProps {
  readonly skills: readonly string[];
  readonly max?: number;
  readonly onClickSkill?: (slug: string) => void;
}

export function SkillBadgeList({ skills, max = 8, onClickSkill }: SkillBadgeListProps) {
  const visible = skills.slice(0, max);
  const overflow = skills.length - max;

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
      {visible.map((s) => (
        <SkillBadge key={s} slug={s} onClick={onClickSkill} />
      ))}
      {overflow > 0 && (
        <span
          style={{
            fontSize: 11,
            color: 'rgba(160,180,255,0.45)',
            alignSelf: 'center',
          }}
        >
          +{overflow} more
        </span>
      )}
    </div>
  );
}
