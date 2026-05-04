# Gamification Reference

Internal mode only. Client mode disables and hides the gamification layer entirely.

## Event bus

The artifact maintains a custom event bus. User actions emit events, subscribers handle XP, achievements, and sound. Adding a new gamification feature is a new subscriber, not a modification to action emission.

Event names:

- `question.option.selected` (single, multi, true_false)
- `question.row.assigned` (numeric_scale, abc_match)
- `question.ranked.changed` (ranked)
- `question.override.used` (free-text override populated)
- `question.hybrid.used` (hybrid composer populated)
- `question.flag.used` (feedback flag populated)
- `section.completed` (every question in a section answered)
- `artifact.completed` (every question in artifact answered)
- `achievement.unlocked` (any achievement triggers)
- `rank.changed` (XP threshold crossed)

## XP rules

Configurable via constants near the top of the artifact, no hardcoded values inline.

```js
const XP_RULES = {
  SINGLE_SELECT: 10,
  MULTI_SELECT_PER_OPTION: 10,
  TRUE_FALSE: 10,
  RANKED_CHANGE: 10,
  NUMERIC_SCALE_PER_ROW: 10,
  ABC_MATCH_PER_ROW: 10,
  OVERRIDE_USED: 5,
  HYBRID_USED: 5,
  FLAG_USED: 5
};

const RANK_THRESHOLD = 200; // XP per rank
```

## Achievement catalog

Seven shipping achievements. Add new achievements by appending to the catalog, not by modifying existing ones.

```js
const ACHIEVEMENTS = [
  {
    id: "first_decision_locked",
    title: "First Decision Locked",
    description: "Locked your first answer",
    xp: 25,
    trigger: "first question.option.selected or question.row.assigned"
  },
  {
    id: "voice_recon",
    title: "Voice Recon",
    description: "Used voice input for the first time",
    xp: 50,
    trigger: "first voice transcript appended to override"
  },
  {
    id: "field_notes",
    title: "Field Notes",
    description: "Used free-text override for the first time",
    xp: 30,
    trigger: "first question.override.used"
  },
  {
    id: "after_action_review",
    title: "After Action Review",
    description: "Flagged feedback for the first time",
    xp: 30,
    trigger: "first question.flag.used"
  },
  {
    id: "section_cleared",
    title: "Section Cleared",
    description: "Answered every question in a section",
    xp: 75,
    trigger: "section.completed"
  },
  {
    id: "tier_master",
    title: "Tier Master",
    description: "Assigned every row in a tier-allocation question",
    xp: 100,
    trigger: "all rows in any abc_match question assigned"
  },
  {
    id: "field_manual_complete",
    title: "Field Manual Complete",
    description: "Answered every question in the artifact",
    xp: 200,
    trigger: "artifact.completed"
  }
];
```

## Sound cues

Web Audio API generates short tones. No external assets, works offline.

```js
const SOUND_CUES = {
  selection: { freq: [880], duration: 80 },
  lock: { freq: [523, 659], duration: 120 },
  achievement: { freq: [523, 659, 784], duration: 350 },
  rankUp: { freq: [523, 659, 784, 1047], duration: 440 }
};
```

Volume defaults to low (0.15 gain). Sound toggle is separate from gamification visibility, so users can have visible XP without sound.

## Rank progression

Rank names come from the active theme's `rankNames` array. Seven ranks total. Threshold is `RANK_THRESHOLD` XP per rank.

- Rank 0 (starter): 0 XP
- Rank 1: 200 XP
- Rank 2: 400 XP
- Rank 3: 600 XP
- Rank 4: 800 XP
- Rank 5: 1000 XP
- Rank 6 (top): 1200 XP

The XP bar in the header shows current rank name, current XP total, and a progress bar to the next rank.

## Adding a new achievement

Pattern:

1. Append to the ACHIEVEMENTS catalog
2. If the trigger is a new condition not covered by existing events, add an event emission in the relevant action handler
3. Increment the version number in the artifact metadata so old saved artifacts can be migrated

The achievement checker subscribes to the event bus on artifact mount. New achievements auto-wire on the next artifact generation.
