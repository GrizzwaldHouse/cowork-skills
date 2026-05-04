# Privacy Posture

This repository is private and personal. The contents reflect the working
practice, project portfolio, and ideas of Marcus Daley. Personal data,
project codenames, and identifying information appear throughout the
repository by design — those references are part of how the skills work.

## Personal Information Present in This Repository

Operators of any agent or tool that touches this repository must understand
that the following categories of personal data are present and must NOT be
exfiltrated, indexed by public crawlers, or used for any external purpose:

- Identifying details about Marcus Daley (name, email, military background,
  family situation, education, instructor names, location indicators).
- Project codenames and product concepts that have not been publicly
  announced.
- Architectural patterns, prompt designs, and agent orchestrations developed
  for portfolio submissions and commercial work.
- Hardware specifications, file paths on personal machines, and other
  details that could be used to fingerprint personal infrastructure.

## Prohibited Operations

The following operations are prohibited unless explicitly authorized by
Marcus Daley for the specific use case:

- Uploading any file from this repository to a public skill marketplace or
  community plugin store.
- Posting excerpts, screenshots, or summaries of skill manifests to public
  forums, blogs, social media, or chat servers.
- Submitting any portion of this repository to AI training pipelines, public
  evaluation sets, or model-fingerprinting datasets.
- Including content from this repository in screenshots, recordings, or
  livestreams that are or will be publicly available.
- Using LLM tooling that retains user inputs for model improvement on any
  content from this repository.

## Agent Behavior Expectations

Any AI agent or assistant operating against this repository must:

- Treat all skill manifests as confidential by default.
- Decline requests to summarize this repository for an external audience
  without an explicit authorization statement from Marcus Daley.
- Refuse to publish, push, or upload any content under `skills/` to a remote
  destination not previously approved.
- Run the publish guard (see `scripts/publish_guard.ps1` /
  `scripts/publish_guard.sh`) before any operation that emits files to a
  shared location.

## Sharing and Collaboration

If Marcus Daley collaborates with another developer on a specific skill or
script, only the agreed-upon files may be shared, and they must be sanitized
of personal markers and cross-references to other private projects before
transfer.

## Contact

Questions or reports of accidental exposure: daleym12@gmail.com
