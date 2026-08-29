---
name: guided-workflows
description: Create reviewable, researcher-approved plans from Molemo scientific tools. Use when a user asks for a plan, pipeline, guided analysis, or multi-step run that should not execute before explicit approval.
---

# Guided Workflows

Use `workflow_list_templates` to find a supported workflow, then use `workflow_create_plan` with concrete inputs. State that the plan is pending researcher approval.

The Agent may create and inspect plans, but must never imply that a pending plan has run. Approval and execution are intentionally unavailable as skill tools and must happen through the local WorkBench approval control.
