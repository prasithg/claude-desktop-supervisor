# Product video tooling notes

Goal: create a launch video fast without turning the repo into a video project too early.

## Recommendation for this launch

Use a two-track approach:

1. Screen Studio for the live product/demo recording.
2. Remotion later for repeatable code-driven launch videos, diagrams, and short social clips.

Reason: today/tomorrow launch needs speed and taste. Screen Studio is built for polished macOS screen demos with automatic zooms, smooth cursor movement, captions/transcripts, and vertical/social export. Remotion is the better long-term skill because Hermes/Claude can generate and edit React code, but it will take longer to get a motion system looking good.

## Options researched

### Screen Studio

Best for: immediate polished product demos from live Mac screen recordings.

What it gives us:

- automatic zoom into cursor/action;
- smooth cursor animation;
- branding/background/export controls;
- vertical social exports;
- transcript/subtitles;
- local processing claims for transcript/audio features;
- fast path to a 60-90 second X/LinkedIn video.

Use it for:

- "live proof" clips of Claude Desktop sidebar / Running state;
- terminal helper output;
- quick architecture walkthrough;
- social video with captions.

Tradeoff: not as agent-editable/reproducible as code. Great for today, less ideal as a repeatable content factory.

### Remotion

Best for: code-driven videos with React.

What it gives us:

- videos as React components;
- parameterized scenes from data;
- real MP4 rendering;
- good fit for coding agents because editing video becomes editing code;
- reusable templates for product launches, diagrams, changelogs, and explainer clips.

Use it for:

- reusable branded video templates;
- animated architecture diagrams;
- launch videos generated from markdown/scripts;
- future "Hermes content studio" workflow.

Tradeoff: licensing needs review for commercial/company use. It also takes setup/design time before it beats Screen Studio for a one-off launch.

### Motion Canvas

Best for: TypeScript/canvas technical animations.

What it gives us:

- animations written in TypeScript;
- generator-function timeline model;
- Vite preview/editor;
- strong for educational/technical motion graphics.

Use it for:

- explainer animations;
- lower-level visualizations;
- cases where canvas/vector animation matters more than React UI composition.

Tradeoff: less aligned with React/product-UI mental model than Remotion. Probably not the first pick for this launch.

### OpenScreen / Cap / OBS-style recorders

Best for: open-source or free recording fallback.

Use if Screen Studio is not installed or not worth buying today. These are more likely to need extra editing passes.

## Proposed Hermes skill: product-video-creation

Trigger:

- user wants a product demo video, launch video, screen-recorded walkthrough, animated explainer, or short social clip for a software project.

Default workflow:

1. Decide the video type:
   - live demo recording;
   - code-driven motion explainer;
   - hybrid screen recording + animated intro/outro.
2. Draft the script first: hook, problem, mechanism, proof, CTA.
3. Create a shot list with exact windows/commands/screens.
4. Choose tool:
   - Screen Studio for immediate live demos on macOS;
   - Remotion for reusable code-driven videos;
   - Motion Canvas for technical animations;
   - ffmpeg for stitching/conversion;
   - browser screenshots/SVG diagrams for assets.
5. Sanitize private data before recording.
6. Record or render clips.
7. Add captions and crop variants:
   - 16:9 for YouTube/LinkedIn;
   - 9:16 for X/shorts if needed;
   - GIF/webm snippet for README.
8. Export and review locally before posting.

Launch-specific choice:

- use Screen Studio or a native macOS recording for live flow capture;
- keep Remotion as the next reusable system, not a blocker for tomorrow.

## Fable Babysitter launch shot list

1. Terminal: run sanitized helper command.

```bash
python3 skills/agent-session-progress/scripts/agent_progress.py --agent claude --limit 5
```

2. Claude Desktop: show the difference between idle/ready and Running if safe.

3. Architecture: show `assets/architecture.html`.

4. Repo: show README section with failure modes.

5. Close: show GitHub repo page once public.

## 60-90 second structure

0-5s: "Claude finished 3 minutes ago. Nobody noticed."

5-20s: failure modes: input box, idle UI, false blocker text, context boundaries.

20-45s: Hermes reads logs and only uses UI when it has to act.

45-65s: architecture diagram: logs -> supervisor -> lanes -> repo/tests -> release.

65-90s: "Not prompt looping. Agent ops." Repo link / CTA.
