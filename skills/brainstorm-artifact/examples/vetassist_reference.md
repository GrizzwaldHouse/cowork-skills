# VetAssist Reference Brainstorm

This is the canonical reference for what a fully-fleshed brainstorm artifact looks like. Marcus produced this for the VetAssist platform on April 28, 2026. Use it as the gold standard for tone, depth, and structure when generating artifacts for new projects.

Notice the patterns: each section groups thematically related decisions, each question has two to eight options with concise trade-off rationale, and the artifact captures decisions across the full project lifecycle from accreditation to launch channel.

---

# VETASSIST BRAINSTORM RESPONSES
Captured: 4/28/2026

## ACCREDITATION PATH

Which accreditation track fits your timeline and goals best?
[x] Both paths in parallel: Start VSO sponsorship now while studying for claims agent exam

Which VSO organization would you prefer to seek sponsorship from?
[x] DAV (Disabled American Veterans): Strong claims focus, peer-led, very aligned with your 100% P&T background
[x] Research all options first: Get introductory meetings before committing to any org
[x] American Legion: Broad membership, strong community chapter presence

How much daily study time can you realistically commit to accreditation prep?
[x] 30-45 min/day: Solid pace, completes Part 14 + M21-1 core in roughly 60-90 days

## PLATFORM POSITIONING

How do you want VetAssist to handle veterans who come in expecting a rating maximizer?
[x] Interstitial compliance screen: Pop-up before any claims-adjacent feature asking them to confirm educational intent

Which veteran audiences should VetAssist prioritize at MVP launch?
[x] Recently separated (ETS/REFRAD in last 2 years): Highest urgency, most digital-native, easiest onboarding
[x] Military spouses and dependents: Often navigating on behalf of veteran, strong advocate multiplier
[x] VSOs and peer support specialists: Power users who will recommend to veterans, multiplier effect
[x] Veterans in VR&E or education transition: Highly motivated, actively navigating VA systems
[x] Vietnam/Gulf War era veterans: Most unclaimed benefits, lowest tech comfort, highest need

For the VA knowledge scraper, what should the plain-English translation priority be?
[x] Compensation claims (38 CFR Part 3, 4): Disability ratings, nexus, effective dates, service connection
[x] Survivor benefits (DIC, SBP): For spouses and dependents navigating posthumous claims
[x] Home loan and grant programs: VA loan entitlement, SAH/SHA grants, VRRAP
[x] Education benefits (GI Bill, VR&E): Chapter 30, 33, 31, VET TEC, STEM eligibility

## VOICE AND AI ENGINE

How should the voice input feature be framed to veterans in the UI?
[x] Story Mode: Tell me about your service, I will help you organize it

Which Hugging Face models should we prioritize integrating for the voice pipeline?
[x] Bio_ClinicalBERT: Medical NER for mapping reported symptoms to clinical terminology
[x] sentence-transformers: Semantic search for matching veteran experiences to relevant CFR sections
[x] WhisperSpeech (TTS): Text-to-speech for reading back structured narratives to veteran
[x] toxic-bert (crisis detection): Already planned, classifies distress signals before AI responds
[x] Microsoft Presidio (PII): Already in your stack for SSN and name scrubbing before AI processing
[x] Whisper (OpenAI, via HF): Best-in-class speech-to-text, self-hostable, no per-call cost after setup

How much should the AI voice engine guide the veteran versus just listening?
[x] Adaptive mode: Veteran chooses: free-form or guided interview at session start

How should the app handle buddy statement or lay statement recording?
[x] Same voice engine, different output template: Shared pipeline but the output swaps to a VA Form 21-10210 compatible format

## MVP LOCK AND SECURITY

What is the hard MVP feature lock? Which features ship first, which are deferred?
[x] SHIP: VA Knowledge Translation (scraper + plain English): Core educational layer, no legal risk, immediate veteran value
[x] SHIP: Voice Narrative Engine (basic): Mic input, Whisper STT, PII scrub, crisis gate, structured output
[x] SHIP: Chat interface with Claude AI reasoning: Already partially built, needs compliance layer hardening
[x] SHIP: Auth + consent (Auth0 + granular scopes): You already chose this in Phase 4 planning
[x] DEFER: Mobile React Native parity: Web-first MVP, mobile after web is hardened

Which compliance and security standards must be met before MVP ships?
[x] WCAG 2.1 AA accessibility: Screen readers, touch targets, reduced motion, high contrast
[x] California AB 489 / SB 243 AI disclosure: Chatbot must disclose it is AI before any substantive interaction
[x] FIPS 140-3 cryptography readiness: FIPS 140-2 expires September 2026, must plan transition now
[x] Crisis detection gate (before AI responds): toxic-bert or equivalent running on every input, no exceptions
[x] VA SB 694 safe harbor documentation: Legal memo confirming educational tool positioning
[x] No PII in logs or analytics: Presidio scrubbing on all stored data, zero SSN/DOB in any log
[x] App Store / Play Store compliance review: Even pre-launch, verify no policy violations before submission

What is the right beta release strategy before public launch?
[x] 20-50 veteran invite-only beta: Controlled, high-touch, you monitor every session manually

Where should VetAssist seek financial support for Hugging Face model hosting and infrastructure?
[x] GitHub Student Developer Pack (you have this): Azure credits, free tools, and partner benefits you should fully map
[x] VA-adjacent foundation grants: Gary Sinise Foundation, TAPS, Mission 22, and others fund veteran tech
[x] 501c3 nonprofit formation: Unlock foundation grants and donation-deductible contributions from supporters
[x] Hugging Face Pro / Enterprise tier grants: HF has veteran and nonprofit pathways worth exploring
[x] AWS Activate for Startups: Free credits for early-stage startups, up to $100K for eligible companies

For the marketing pitch agent, what tone and channel should anchor the launch story?
[x] LinkedIn as primary channel for MVP launch: Veteran community is active on LinkedIn, Peter and Higher Heroes network
[x] VSO newsletter / post placement as primary: Bypass algorithms entirely, trusted channel with the right audience
[x] Founder story-first (your submarine service): Personal credibility, emotional resonance, differentiates from faceless tech
[x] Data-first (how many veterans are leaving benefits unclaimed): Shock value, quantified need, good for grant applications and press
