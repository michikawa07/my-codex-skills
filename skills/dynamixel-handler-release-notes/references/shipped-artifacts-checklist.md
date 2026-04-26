# Shipped Artifacts Checklist

Use this checklist before finalizing release notes.

## Final Tree Checks

- Inspect the final tagged tree, not only intermediate commits.
- Check whether the shipped package actually exposes the behavior described in the code.
- Confirm whether docs, defaults, examples, and launch entrypoints make the feature reachable in normal use.

## Artifacts To Inspect

- config files
- msg definitions
- launch files
- example nodes
- utility scripts and executables
- README snippets
- package manifests or build files when they change distribution behavior

## Questions To Ask

- Does this change alter a distributed interface or sample usage?
- Does the final package behavior match what the code suggests?
- Is the feature usable without hidden setup or undocumented parameters?
- Is a small code change actually important because it changes a shipped example or default?
- Is this note describing an externally visible effect, or only an internal implementation detail?
