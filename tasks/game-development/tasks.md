# Game Development Task Templates

Reusable task templates for game development including Unreal Engine, Unity, and general game design workflows.

---

## New Game Feature Implementation

### Design Phase
- [ ] Write game design document (GDD) section for the feature
- [ ] Define player-facing behavior (what does the player experience?)
- [ ] Define game mechanics (rules, triggers, conditions, outcomes)
- [ ] Identify required assets (meshes, textures, sounds, animations, VFX)
- [ ] Define UI/HUD requirements
- [ ] Plan progression/balance impact (does this change difficulty?)

### Implementation Phase
- [ ] Create feature branch: `feature/[name]`
- [ ] Implement core gameplay logic
- [ ] Create/import required assets
- [ ] Set up collision and physics
- [ ] Implement sound effects and visual feedback
- [ ] Add UI/HUD elements
- [ ] Configure input bindings

### Polish Phase
- [ ] Add particle effects / VFX
- [ ] Add screen shake, camera effects
- [ ] Tune timing and "game feel"
- [ ] Add audio (SFX, ambient, music triggers)
- [ ] Balance difficulty (playtest 5+ times, adjust values)

### Testing Phase
- [ ] Test on target platforms
- [ ] Check frame rate impact (profile if needed)
- [ ] Test edge cases (what if player does X during Y?)
- [ ] Test multiplayer interactions (if applicable)
- [ ] Get 3+ playtest feedback sessions

---

## Level / Map Design

### Planning
- [ ] Define level purpose (tutorial, challenge, boss, exploration, hub)
- [ ] Sketch top-down layout (paper or digital)
- [ ] Plan player flow (start > objectives > end)
- [ ] Identify key landmarks for navigation
- [ ] Plan enemy/NPC placement
- [ ] Plan pickup/collectible placement
- [ ] Define lighting mood and time of day

### Construction
- [ ] Block out level with basic geometry (BSP/ProBuilder/primitives)
- [ ] Playtest blockout for flow and timing
- [ ] Replace blockout with final meshes/assets
- [ ] Add lighting (directional + point/spot lights)
- [ ] Add environment props and decoration
- [ ] Place spawners, triggers, and gameplay actors
- [ ] Add invisible walls/kill volumes at boundaries

### Polish
- [ ] Add fog, post-processing effects
- [ ] Add ambient sounds and music zones
- [ ] Optimize with LODs, occlusion culling, distance culling
- [ ] Add skybox/sky atmosphere
- [ ] Test performance (target frame rate on min spec)
- [ ] Playtest complete level 5+ times

---

## Unreal Engine Blueprint / Actor

### Setup
- [ ] Create Blueprint class (select parent: Actor, Pawn, Character, GameMode, etc.)
- [ ] Add required components (StaticMesh, Skeletal Mesh, Collision, Audio, Particles)
- [ ] Configure component transforms (location, rotation, scale)
- [ ] Set up collision profiles (overlap vs block)
- [ ] Configure physics properties if needed (mass, gravity, damping)

### Logic
- [ ] Implement BeginPlay initialization
- [ ] Implement Tick logic (minimize per-frame work)
- [ ] Set up event dispatchers for communication
- [ ] Implement interaction system (overlap events, line traces)
- [ ] Add state management (enum-based state machine recommended)
- [ ] Handle edge cases (what if spawned mid-game, what if destroyed early)

### Integration
- [ ] Test in isolation (spawn in empty level)
- [ ] Test in target level (does it interact correctly with everything?)
- [ ] Profile performance impact
- [ ] Document Blueprint purpose and public variables
- [ ] Add to actor palette / spawner system

---

## Character / AI Agent

### Core Setup
- [ ] Create Character Blueprint (or inherit from existing base)
- [ ] Configure capsule collision
- [ ] Set up skeletal mesh and animation blueprint
- [ ] Configure character movement (speed, jump, crouch)
- [ ] Set up AI controller and behavior tree (for NPCs)

### AI Behavior
- [ ] Define behavior states (idle, patrol, chase, attack, flee, search)
- [ ] Implement perception system (sight, hearing, damage)
- [ ] Create behavior tree with appropriate tasks and decorators
- [ ] Implement navigation (NavMesh, pathfinding)
- [ ] Add combat logic (attack patterns, cooldowns, damage)
- [ ] Add avoidance and group behavior (if multiple AI)
- [ ] Tune detection ranges and response times

### Animation
- [ ] Set up animation state machine
- [ ] Implement locomotion blend space (idle > walk > run)
- [ ] Add action animations (attack, hit reaction, death)
- [ ] Add transitions and blend times
- [ ] Implement animation montages for one-shots
- [ ] Add root motion if needed

---

## Game UI / HUD

### Design
- [ ] Wireframe all HUD elements (health, ammo, minimap, score, etc.)
- [ ] Define which info is always visible vs contextual
- [ ] Choose font that fits game aesthetic (see typography-reference.md)
- [ ] Define color scheme matching game mood
- [ ] Plan responsive scaling for different resolutions

### Implementation
- [ ] Create Widget Blueprint / UI prefab
- [ ] Bind data to gameplay variables (health, score, ammo)
- [ ] Add animations for value changes (pulse, flash, slide)
- [ ] Implement damage indicators (screen edge red, vignette)
- [ ] Add crosshair / reticle system
- [ ] Implement menu system (pause, settings, inventory)
- [ ] Add controller/gamepad support for all menus

### Polish
- [ ] Add sound effects for UI interactions
- [ ] Add haptic feedback for controller (if applicable)
- [ ] Test at all target resolutions (1080p, 1440p, 4K)
- [ ] Ensure colorblind-friendly (use shapes + color, not color alone)
- [ ] Test with different input methods (mouse, controller, touch)

---

## Multiplayer / Networking

- [ ] Define networking model (client-server, P2P, dedicated server)
- [ ] Identify which actors need replication
- [ ] Implement server-authoritative logic for critical gameplay
- [ ] Implement client prediction for responsive feel
- [ ] Handle lag compensation
- [ ] Test with simulated latency (100ms, 200ms, 500ms)
- [ ] Implement lobby/matchmaking
- [ ] Add disconnect handling and rejoin
- [ ] Implement anti-cheat measures for critical systems

---

## Obstacle Course / Arena Design (GAR Project)

### Planning
- [ ] Define difficulty level (easy, medium, hard)
- [ ] Plan course layout (start position, path, checkpoints, end)
- [ ] Plan hazard types and placement (DamagePickups)
- [ ] Plan wall placement for navigation challenges
- [ ] Plan pickup placement (health, ammo) for balance

### Building with MCP Tools
- [ ] Place spawner(s) at start position: `spawn_gar_spawner`
- [ ] Place walls for course structure: `spawn_gar_wall`
- [ ] Place damage pickups as hazards: `spawn_gar_damage_pickup`
- [ ] Place health pickups for recovery: `spawn_gar_health_pickup`
- [ ] Place ammo pickups: `spawn_gar_ammo_pickup`
- [ ] Or use `create_gar_obstacle_course` for auto-generation
- [ ] Place AI agents for combat: `spawn_gar_agent`

### Testing
- [ ] Walk through course manually
- [ ] Verify difficulty is appropriate (not too easy, not unfair)
- [ ] Check all pickups are reachable
- [ ] Verify spawners work correctly
- [ ] Test AI agent behavior in the space
- [ ] Adjust spacing, difficulty, and pickup count

---

## Performance Optimization (Games)

- [ ] Profile with engine tools (Unreal Stat commands / Unity Profiler)
- [ ] Identify frame rate drops and their causes
- [ ] Common checks:
  - [ ] Draw calls (batch materials, merge meshes)
  - [ ] Triangle count (LODs, mesh simplification)
  - [ ] Texture memory (compression, streaming, mipmaps)
  - [ ] Physics complexity (simplify collision, reduce active bodies)
  - [ ] AI pathfinding cost (NavMesh optimization, update frequency)
  - [ ] Particle systems (reduce count, use GPU particles)
  - [ ] Garbage collection spikes (object pooling)
  - [ ] Shader complexity (reduce instructions, use LOD materials)
- [ ] Set performance budget per feature
- [ ] Test on minimum spec hardware
- [ ] Test with maximum entity count

---

## Build & Release

- [ ] Freeze features (no new features, only bug fixes)
- [ ] Complete all critical bug fixes
- [ ] Run full QA pass on all platforms
- [ ] Optimize build size (remove unused assets, compress textures)
- [ ] Configure build settings (shipping, release mode)
- [ ] Package for target platforms
- [ ] Test packaged build (not just editor)
- [ ] Create release notes / changelog
- [ ] Upload to distribution platform
- [ ] Monitor crash reports post-launch
