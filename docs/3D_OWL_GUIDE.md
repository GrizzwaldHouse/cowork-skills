# 3D Owl Mascot Implementation Guide

## Overview

This guide shows you how to create 3D owl sprites for the OwlWatcher mascot and integrate them into the app.

## Step 1: Choose Your Style

### Option A: Stylized Low-Poly (Recommended for Beginners)
- **Visual**: Clean geometric shapes, friendly appearance
- **Difficulty**: Easiest to create in Blender
- **Best for**: Modern UI, playful aesthetic

### Option B: Realistic Barn Owl
- **Visual**: Photo-realistic feathers and textures
- **Difficulty**: Advanced (requires good texturing skills)
- **Best for**: Professional security app aesthetic

### Option C: Cartoon Wise Owl
- **Visual**: Rounded shapes, big expressive eyes
- **Difficulty**: Medium (requires character modeling skills)
- **Best for**: Friendly, approachable design

## Step 2: Generate Sprites

### Method 1: AI Image Generation (Fastest)

Use an AI image generator like DALL-E, Midjourney, or Stable Diffusion:

#### For Option A (Low-Poly):
```
Prompt template:
"3D low-poly owl mascot character, front-facing view, geometric shapes,
warm brown and gold colors, large friendly eyes, sitting pose,
dark navy night sky background, professional 3D render, isometric style,
soft lighting, Pixar quality, 1024x1024 resolution, PNG with transparency

STATE: [insert state description below]"

State descriptions:
1. SLEEPING: "eyes closed, head tucked down, peaceful resting expression"
2. WAKING: "one eye half-open, stretching wings slightly, yawning"
3. IDLE: "alert posture, calm expression, looking straight forward"
4. SCANNING: "head turned 15 degrees to left, focused eyes, attentive"
5. CURIOUS: "head tilted to side, wide eyes, inquisitive look"
6. ALERT: "wider eyes, feathers slightly raised, very attentive"
7. ALARM: "startled expression, feathers puffed up, eyes very wide"
8. PROUD: "chest out, confident smile, wings slightly spread"
```

#### For Option B (Realistic):
```
"Photorealistic 3D barn owl, beautiful detailed feathers,
cream and gold plumage, dark eyes, professional studio lighting,
dark navy background, front view, sitting on wooden branch,
4K quality render, cinematic lighting, PNG with transparency

STATE: [use same state descriptions as above]"
```

#### For Option C (Cartoon):
```
"3D cartoon owl character, big expressive eyes, rounded friendly shapes,
vibrant brown and gold colors, sitting pose, dark background,
professional 3D animation style, Disney/Pixar quality, soft shadows,
1024x1024 pixels, PNG with transparency

STATE: [use same state descriptions as above]"
```

### Method 2: Blender (Full Control)

If you want to create your own owl in Blender:

1. **Create Base Model**:
   - Use basic shapes (spheres, cones, cylinders)
   - Model head, body, wings, eyes, beak
   - Keep polygon count low (under 5000 polys for Option A)

2. **Add Materials**:
   - Brown body material (#8B7355)
   - Gold accent feathers (#C9A94E)
   - Dark eyes with glossy shader
   - Use Principled BSDF shader

3. **Setup Camera**:
   - Front view, slightly above owl
   - Distance: 3-4 Blender units
   - Focal length: 50mm

4. **Lighting**:
   - 3-point lighting setup
   - Key light: 45° angle, warm color
   - Fill light: opposite side, softer
   - Rim light: behind and above

5. **Render Settings**:
   - Resolution: 1024x1024
   - Samples: 128 (Cycles) or 32 (Eevee)
   - Transparent background enabled
   - Output format: PNG with alpha

6. **Create Each State**:
   - Use pose bones or shape keys for expressions
   - Render each state separately
   - Save as `owl_3d_[state].png`

## Step 3: Prepare Sprite Files

1. **Create sprite directory**:
   ```
   C:\ClaudeSkills\scripts\gui\assets\owl_3d\
   ```

2. **Name your files exactly**:
   - `owl_3d_sleeping.png`
   - `owl_3d_waking.png`
   - `owl_3d_idle.png`
   - `owl_3d_scanning.png`
   - `owl_3d_curious.png`
   - `owl_3d_alert.png`
   - `owl_3d_alarm.png`
   - `owl_3d_proud.png`

3. **Image requirements**:
   - Format: PNG with transparency
   - Size: 512x512 or 1024x1024 pixels
   - Background: Transparent (alpha channel)
   - File size: Keep under 500KB each for fast loading

## Step 4: Integrate into App

Once you have your sprites, integrate them:

1. **Update main_window.py**:
   ```python
   # Replace line that imports OwlWidget:
   from gui.widgets.owl_3d_widget import Owl3DWidget

   # Replace line that creates owl widget:
   self._owl = Owl3DWidget(owl_size=OWL_HEADER_SIZE)
   ```

2. **Test the integration**:
   ```bash
   python scripts/gui/app.py
   ```

## Step 5: Quick Test Without Sprites

If you want to test the code before creating sprites:

1. The widget will show state labels even without sprites
2. You'll see error messages in the log about missing sprites
3. This confirms the code integration works

## Recommended Workflow

**Fastest path to working 3D owl**:

1. ✅ Choose **Option A** (Low-Poly) for easiest creation
2. ✅ Use **AI Image Generation** (DALL-E 3 or Midjourney)
3. ✅ Generate all 8 states using the prompts above
4. ✅ Save to `scripts/gui/assets/owl_3d/` directory
5. ✅ Update `main_window.py` to use `Owl3DWidget`
6. ✅ Run app and enjoy your 3D owl!

## Example Prompts Ready to Use

### Complete prompt for DALL-E 3 (Sleeping state):
```
Create a 3D low-poly owl mascot character in sleeping pose. The owl should have:
- Geometric, angular shapes (low polygon count)
- Warm brown body (#8B7355) with gold accent feathers (#C9A94E)
- Large friendly eyes that are CLOSED
- Head tucked down in peaceful resting position
- Sitting pose on a small branch
- Dark navy night sky background (#0D1B2A)
- Professional 3D render with soft lighting
- Isometric/front-facing view
- Clean, Pixar-quality style
- 1024x1024 resolution
- Transparent PNG background

The owl should look friendly and approachable, perfect for a security monitoring app mascot.
```

Just replace "sleeping pose" and "eyes CLOSED, head tucked" with other states!

## Troubleshooting

**Sprites not showing?**
- Check file paths are exact: `owl_3d_sleeping.png` not `owl_sleeping.png`
- Verify sprites are in `scripts/gui/assets/owl_3d/` directory
- Check console for error messages about missing files

**Crossfade not smooth?**
- Ensure sprites are same size (all 512x512 or all 1024x1024)
- Check that transparency is properly set in PNG alpha channel

**Sprites look blurry?**
- Use higher resolution source (1024x1024 minimum)
- Enable SmoothTransformation in QPixmap scaling (already done)

## Next Steps

After you have your 3D owl working:
1. Fine-tune crossfade duration in constants.py
2. Add subtle animations (breathing, blinking) if desired
3. Consider adding multiple viewing angles for variety
4. Optimize sprite file sizes for faster loading
