# Setting Up AI to Work Like You

The best way to use AI on a codebase is not to use a generic assistant - it is to make the AI an extension of yourself. This means teaching it your conventions, your style, and your decisions, so it stops making choices you have to undo.

This is not a beginner tutorial. Read the code first. Understand the architecture. Then come back here.

---

## The Core Idea

AI tools work best when they have context. Without it, they guess - and they guess generically. The goal is to give them enough signal that their output looks like yours, not like a Stack Overflow answer.

There are three layers to this:

1. **Project context** - what the codebase is, how it works, what decisions were made and why
2. **Your conventions** - commit style, naming, what you never do, what you always do
3. **Persistent memory** - so the AI does not forget between sessions

---

## Layer 1 - Project Context (AGENTS.md)

`AGENTS.md` at the repo root is read by most AI coding tools automatically (Claude Code, OpenCode, Cursor, Copilot Workspace, etc.).

Write it like you are briefing a new developer who is smart but has never seen your repo. Include:

- What the project is and where the code came from
- Directory map with annotations - not just file names, but what each file does
- Architecture decisions and why they were made
- Critical paths - files that are easy to break, traps to avoid
- What NOT to do (just as important as what to do)

This repo's [AGENTS.md](../AGENTS.md) is a working example. Read it to see the format.

Bad AGENTS.md:
```
This is a Python project. Use snake_case.
```

Good AGENTS.md:
```
core/ has no Rich/Typer imports - it is the public library API. Keep it that way.
style= params on Rich Table do not resolve theme names. Use literal hex #22c55e bold.
Windows command line limit is 32767 chars. segmenter.py chunks at 1500 cuts. Do not remove this.
```

The difference is specificity. Generic rules the AI already knows are useless. Document what the AI cannot infer from reading the code.

---

## Layer 2 - Your Conventions (Custom Instructions)

Every major AI tool has a way to set persistent instructions that apply across all sessions.

**Claude Code** - `~/.claude/CLAUDE.md` (global) or `CLAUDE.md` at repo root (project-scoped):

```markdown
Commit style: (add) / (fix) / (update) prefix. No Co-Authored-By trailer.
Never use em dashes. No inline code comments.
Banner markup: [accent]AMV[/][white bold]erge[/] - never swap the colors.
```

**Cursor** - `.cursorrules` at repo root or Settings > Rules for AI.

**OpenCode** - `OPENCODE.md` at repo root (this repo has one).

**Copilot** - `.github/copilot-instructions.md`.

Write these in first person as instructions, not descriptions. "Never add Co-Authored-By" not "Co-Authored-By should not be added."

---

## Layer 3 - Persistent Memory

Most AI tools have some form of memory that persists between sessions. Use it.

After a session where the AI learned something about your preferences - a correction you made, a pattern you confirmed - tell it explicitly:

```
Remember: I want one commit per logical change, not one big commit at the end.
Remember: I never want trailing summary paragraphs in responses.
```

Claude Code writes these to `~/.claude/projects/<project>/memory/`. You can read and edit them directly if the AI stored something wrong.

The memory system is only useful if you maintain it. Delete stale entries. Correct wrong ones. A bad memory is worse than no memory - it confidently does the wrong thing.

---

## Making the AI Match Your Output Style

The fastest way to calibrate style is to show, not tell.

**Method 1 - Show existing work:**
```
Here is a commit message I wrote: "(fix) wizard: handle KeyboardInterrupt during path input"
Here is another: "(add) core: PyAV decode fallback for pathological keyframe encodes"
Write all future commit messages in this style.
```

**Method 2 - Show a rejection:**
```
You wrote: "feat: add keyboard interrupt handling"
I want: "(fix) wizard: handle KeyboardInterrupt during path input"
Remember this style for all commits.
```

Rejections are more memorable than approvals. When the AI gets something wrong and you correct it, that is the highest-signal moment to force a memory write.

**Method 3 - The AGENTS.md feedback loop:**

When the AI makes a mistake that could have been prevented by better documentation, add it to AGENTS.md immediately. Do not just correct the AI - fix the source so it never happens again.

Example: the AI kept using `style="accent bold"` on Rich Table kwargs, which throws `MissingStyle`. After the second time, this went into AGENTS.md:

```
Rich style= params: theme names only resolve inside markup [accent]text[/].
Never in style=, header_style=, title_style= - use literal hex #22c55e bold.
```

---

## Workflow That Actually Works

1. Write `AGENTS.md` before starting a session, not after
2. Start sessions by telling the AI to read `AGENTS.md` first
3. Correct mistakes immediately and ask the AI to remember the correction
4. After the session, update `AGENTS.md` with anything it got wrong that was not already documented
5. Keep sessions focused - one feature or one fix. Long sessions drift.

---

## What AI Cannot Replace

- Knowing what to build. AI optimizes toward a goal. If the goal is wrong, the output is wrong faster.
- Code review judgment. AI will pass bad patterns if they look syntactically clean.
- Architecture decisions. AI defaults to the most common pattern, not the right one for your constraints.
- Debugging novel failures. AI pattern-matches to known errors. New failure modes confuse it.

Use AI for: mechanical implementation of a decision you already made, documentation, repetitive edits across many files, writing test cases for logic you understand.

Do not use AI for: deciding what the architecture should be, reviewing security-sensitive code, anything where "looks right" is not the same as "is right."
