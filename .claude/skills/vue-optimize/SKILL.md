---
name: vue-optimize
description: Analyzes Vue component structure for performance issues and code-reuse opportunities, then delegates fixes to vue-expert. Use when asked to review, audit, or optimize Vue components/composables for performance or duplication.
---

# Vue Component Structure Optimizer

Analyzes Vue 3 components in `client/src/` for performance issues and code-reuse
opportunities, reports findings, then delegates fixes to the `vue-expert` subagent
(per this repo's mandatory rule for any `.vue` create/modify).

## Step 1: Determine Scope

- If the user passed specific file(s)/dir(s) as arguments, analyze only those.
- If the user says "all" / "whole app" / "entire client", analyze every file in
  `client/src/views/`, `client/src/components/`, and `client/src/composables/`.
- **Otherwise (default, no arguments)**: analyze only files that differ from `main`.
  Run:
  ```bash
  git diff --name-only main...HEAD -- client/src
  git status --porcelain -- client/src
  ```
  Union both lists (uncommitted + committed-since-main), then filter to
  `*.vue` and `client/src/composables/*.js`. If the result is empty, tell the
  user there's nothing changed to analyze and stop.

## Step 2: Analyze Each File

Read every file in scope. For each, check against the two categories below.
Reference concrete line numbers — don't generalize.

### Performance checks

- **Methods vs computed**: template calls a `method()` for a derived value that
  doesn't depend on an event — should be `computed()` (recalculates every render
  instead of caching). See `client/src/App.vue`/views for the existing computed
  pattern to match.
- **`v-for` keys**: any `:key="index"` or missing `:key` — must use a stable
  field (`sku`, `id`, `month`). This is a known project pitfall (see CLAUDE.md
  "Common Issues").
- **Unvalidated date parsing in hot paths**: `new Date(x).getMonth()` etc.
  called inside a loop/computed without an `isNaN` guard — wasted work on
  invalid dates plus a correctness bug.
- **Deep/expensive watchers**: `watch(source, cb, { deep: true })` on large
  arrays/objects where a narrower computed or targeted watch would do less
  work.
- **Reactivity granularity**: large reactive objects mutated wholesale when
  only a slice changes; candidates for splitting into smaller refs or using
  `shallowRef`.
- **Repeated work in templates**: non-trivial expressions or chained
  `.filter().map()` written inline in the `<template>` instead of a
  `computed` — recomputes on every re-render instead of caching.
- **Unnecessary full-list re-filtering**: client-side filter logic that
  re-scans the full dataset on every keystroke/filter change without any
  memoization, when the dataset is large.

### Code-reuse checks

- **Duplicate script logic across files**: near-identical `loadData`,
  filtering, or date-formatting logic repeated in 2+ views — extract to a
  composable in `client/src/composables/` (project already does this for
  `useFilters`).
- **Duplicate template/markup patterns**: repeated card/table/chart markup
  across views that could become a shared component in
  `client/src/components/`.
- **Duplicate API boilerplate**: same try/catch/loading/error scaffolding
  repeated per view instead of a shared `useAsyncData`-style composable.
- **Magic values**: repeated literals (status strings, colors, thresholds)
  that should be a shared constant instead of copy-pasted.

## Step 3: Report Findings

Present findings grouped by category (Performance, Code Reuse), each with:
`file:line` — issue — why it matters — suggested fix (one line).

Skip this step's write-up if there's nothing worth flagging in a category —
don't manufacture filler findings.

## Step 4: Apply Fixes via vue-expert

After presenting findings, ask the user if they want fixes applied (unless
they already said so, e.g. "optimize and fix it").

If applying fixes:
- **Never edit `.vue` files directly from this skill** — delegate to the
  `vue-expert` subagent per CLAUDE.md's mandatory rule.
- Batch by file: one `vue-expert` task per file (or per tightly-related
  group, e.g. a view + the composable it should extract logic into), with
  the exact findings and target line numbers from Step 3 — not a vague
  "optimize this file" instruction.
- For cross-file extractions (new composable/component used by multiple
  views), do it as a single `vue-expert` task covering the new file plus all
  call sites, so it lands as one consistent change.
- `client/src/composables/*.js` are plain JS, not `.vue` — vue-expert still
  owns them (they're in its file scope per `.claude/agents/vue-expert.md`),
  but the mandatory-delegation rule specifically covers `.vue` files.

## Step 5: Verify

After fixes land, run `/test` or ask `code-reviewer` to review the diff.
Report what changed and what's left unaddressed (e.g. reuse opportunities
the user chose to skip).
