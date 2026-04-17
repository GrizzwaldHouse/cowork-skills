---
name: video-generation
description: "Create videos programmatically using Remotion (React + TypeScript). Use when the user wants to generate videos from code, create animated presentations, motion graphics, social media clips, data visualization videos, or mentions Remotion, programmatic video, or 'video from code'. Also trigger for animated explainers, promotional videos, or any task where video is the output format and code-based generation is appropriate."
---

# Video Generation with Remotion

Remotion renders React components as video frames -- write React, get MP4. Every frame is a function of the current time, giving precise control over every pixel at every moment.

## Setup

```bash
npx create-video@latest my-video
cd my-video
npm start           # Preview at localhost:3000
```

## Core Concepts

### Composition (Video Definition)
```tsx
import { Composition } from 'remotion';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MyVideo"
      component={MyVideo}
      durationInFrames={300}  // 10 seconds at 30fps
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

### useCurrentFrame & useVideoConfig
```tsx
import { useCurrentFrame, useVideoConfig } from 'remotion';

const MyVideo: React.FC = () => {
  const frame = useCurrentFrame();          // Current frame number (0-based)
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const progress = frame / durationInFrames; // 0 to 1

  return (
    <div style={{ opacity: progress }}>
      Frame {frame} of {durationInFrames}
    </div>
  );
};
```

### Sequences (Timing Sections)
```tsx
import { Sequence } from 'remotion';

const MyVideo: React.FC = () => {
  return (
    <>
      <Sequence from={0} durationInFrames={90}>
        <TitleSlide />
      </Sequence>
      <Sequence from={90} durationInFrames={120}>
        <ContentSlide />
      </Sequence>
      <Sequence from={210} durationInFrames={90}>
        <OutroSlide />
      </Sequence>
    </>
  );
};
```

## Animation

### interpolate (Linear Mapping)
```tsx
import { interpolate, useCurrentFrame } from 'remotion';

const MyComponent: React.FC = () => {
  const frame = useCurrentFrame();

  // Map frame 0-30 to opacity 0-1, clamp outside range
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Slide in from left
  const translateX = interpolate(frame, [0, 30], [-100, 0], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{ opacity, transform: `translateX(${translateX}%)` }}>
      Hello
    </div>
  );
};
```

### spring (Physics-Based)
```tsx
import { spring, useCurrentFrame, useVideoConfig } from 'remotion';

const MyComponent: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: {
      damping: 10,     // Higher = less bounce
      stiffness: 100,  // Higher = faster
      mass: 1,         // Higher = heavier/slower
    },
  });

  return <div style={{ transform: `scale(${scale})` }}>Bounce!</div>;
};
```

### Easing Functions
```tsx
import { interpolate, Easing } from 'remotion';

const value = interpolate(frame, [0, 60], [0, 1], {
  easing: Easing.bezier(0.25, 0.1, 0.25, 1), // CSS ease equivalent
  // Or: Easing.inOut(Easing.ease), Easing.bounce, Easing.elastic(1)
});
```

## Media

```tsx
import { Img, Video, Audio, OffthreadVideo, staticFile } from 'remotion';

// Images (from public/ folder)
<Img src={staticFile('logo.png')} style={{ width: 200 }} />

// Video overlay (use OffthreadVideo for better performance)
<OffthreadVideo src={staticFile('background.mp4')} />

// Audio
<Audio src={staticFile('music.mp3')} volume={0.5} />

// Remote URLs work too
<Img src="https://example.com/image.jpg" />
```

## Common Patterns

### Slide Show
```tsx
const slides = ['Intro', 'Problem', 'Solution', 'CTA'];
const framesPerSlide = 90; // 3 seconds each

const SlideShow: React.FC = () => {
  return (
    <>
      {slides.map((text, i) => (
        <Sequence key={i} from={i * framesPerSlide} durationInFrames={framesPerSlide}>
          <Slide text={text} />
        </Sequence>
      ))}
    </>
  );
};
```

### Data-Driven Charts
```tsx
const AnimatedBar: React.FC<{ value: number; delay: number }> = ({ value, delay }) => {
  const frame = useCurrentFrame();
  const height = interpolate(frame - delay, [0, 30], [0, value], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return <div style={{ height: `${height}%`, width: 40, background: '#3B82F6' }} />;
};
```

### Text Reveal (Character by Character)
```tsx
const TextReveal: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const charsToShow = Math.floor(interpolate(frame, [0, 60], [0, text.length], {
    extrapolateRight: 'clamp',
  }));
  return <span>{text.slice(0, charsToShow)}</span>;
};
```

## Rendering

```bash
# Render to MP4 (H.264)
npx remotion render MyVideo out/video.mp4

# Render specific frames
npx remotion render MyVideo out/video.mp4 --frames=0-90

# Different codec
npx remotion render MyVideo out/video.webm --codec=vp8
npx remotion render MyVideo out/video.mov --codec=prores

# GIF output
npx remotion render MyVideo out/animation.gif

# Custom resolution
npx remotion render MyVideo out/video.mp4 --scale=0.5

# Preview (dev server)
npx remotion preview
```

## Performance Tips

- Use `React.memo()` on components that don't change every frame
- Use `staticFile()` for assets in the `public/` folder (optimized loading)
- Use `OffthreadVideo` instead of `Video` for background videos
- Use `prefetch()` for remote assets to avoid loading delays
- Keep expensive calculations outside the render function
- Use `delayRender()` / `continueRender()` for async data loading
