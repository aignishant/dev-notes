# Section 6 — TIPCommon & SOAR SDK

This is the engineering heart of the project. Expect the majority of your senior/lead technical questions here — base classes, extraction patterns, validation, the Template Method design.

## What you'll learn

- What TIPCommon is and why it exists
- The `Action`, `Connector`, `Job` base-class architecture (Template Method)
- Extraction helpers (`extract_action_param`, `extract_connector_param`, `extract_job_param`)
- `ParameterValidator` and custom validation
- `EnvironmentCommon` and its role
- How the SOAR SDK interacts with TIPCommon
- Version management across wheel versions

## Pages

1. **[TIPCommon Library](tipcommon-overview.md)** — what's inside
2. **[Base Classes](base-classes.md)** — Action, Connector, Job deep dive
3. **[Extraction & Validation](extraction-validation.md)** — helper patterns
4. **[EnvironmentCommon](envcommon.md)** — environment handling
5. **[SOAR SDK](soar-sdk.md)** — how it fits
6. **[Interview Q&A](questions.md)**

!!! tip "The lead-signal question"
    *"Why did we move from `@output_handler` to class-based Actions?"* The answer is **Template Method + consistent error wrapping + testability + separation of concerns**. Nail this.
