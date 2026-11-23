# Pipeline Progress

- run_id            : orchestrator
- archetype         : brownfield-app-dev (specialization: agentic-app, tier: poc)
- methods           : (not set)
- run_mode          : gated — stop and wait for human confirmation after every phase's last task, plus any task whose own pipeline.yaml entry sets human_review: true
- plan_status       : inprogress
- circuit_breaker   : ok
- open_gates        : (none)
- active_reqs       : (none)
- last_checkpoint   : task:onboarding:import:inprogress

## ◉ onboarding  (inprogress)
- ◉ [import] Confirm the existing application is present, scaffold .aah/ over it without touching history, import its codebase intelligence, and arm the ports registry  (inprogress)
- ○ [connect-github] Register the existing GitHub repository, push develop, enable version control and provision labels and governance-team access  (pending)

## ○ discuss  (pending)
- ○ [discuss] Capture intent against the existing system, record the improvement type, walk the decisions, approve the PRD, and compile the activated ports  (pending)

## ○ architecture  (pending)
- ○ [arch] Define epics, module boundaries against the existing structure, and architecture with the activated design ports  (pending)

## ○ plan  (pending)
- ○ [plan] Produce standards and module features that account for the existing codebase, the dependency DAG, and GitHub implementation issues  (pending)

## ○ build  (pending)
- ○ [build] Implement and review each module against the existing code, validate the complete build, refresh the codebase intelligence, and promote to develop  (pending)

## ○ deploy  (pending)
- ○ [deploy] Pass governance and security checks, redeploy through the existing release process with staged validation and rollback evidence, and record outputs  (pending)
