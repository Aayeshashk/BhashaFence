

\# AEGIS — Novelty Assessment



\## Assessment date

2026-10-15



\## Purpose

Refine the project contribution using existing agent-security

benchmarks, enforcement systems, and prompt-injection research.



\## Confirmed competing work



\### AgentDojo

Repository:

https://github.com/ethz-spylab/agentdojo



Already provides agent tasks, prompt-injection scenarios,

defense comparisons, and security-versus-utility evaluation.



\### Agent Policy Gateway

Repository:

https://github.com/howardhsieh/agent-policy-gateway



Already provides policy enforcement, information-flow tracking,

per-value taint, audit logging, and a reproducible comparison

across defense paradigms.



\### Microsoft PyRIT

Repository:

https://github.com/microsoft/PyRIT



Already provides an extensible AI red-teaming and evaluation

framework.



\### BrowseSafe++

Paper:

https://arxiv.org/abs/2610.17457



Studies prompt-injection detection across webpage contexts,

languages, and browser representations, including screenshots.



\### OWASP GenAI Security

Reference:

https://genai.owasp.org/llmrisk/llm062025-excessive-agency/



Provides guidance on excessive agency and the risks of

overly broad tool permissions and manipulated agent behavior.



\## Features that are not independently novel

\- A generic AI-agent security gateway

\- Basic tool-call allow/deny policies

\- Taint tracking by itself

\- An audit-log dashboard

\- A generic prompt-injection detector

\- A multilingual detector without a distinct validated contribution



\## Revised research direction



Investigate whether the action-level security outcomes of

tool-using agents change when semantically equivalent indirect

prompt-injection scenarios are expressed in English, Hindi,

Marathi, and code-mixed text.



Compare:

1\. An agent without additional defenses.

2\. Content-filtering or rules-based defense.

3\. Tool-execution policy enforcement.

4\. Provenance-aware enforcement, if feasible.



\## Primary outcome measures

\- Successful unauthorized actions

\- Legitimate task completion

\- False-positive blocks

\- Policy decisions and explanations

\- Execution overhead



\## Hypothesis

Security outcomes may differ across language variants even when

the intended malicious objective remains equivalent. Tool-level

enforcement may reduce unauthorized actions, but its effect on

legitimate task completion must also be measured.



This hypothesis requires empirical testing.



\## Important limitations

\- A language-robustness evaluation is not automatically novel.

\- BrowseSafe++ already overlaps with multilingual detection.

\- Existing policy gateways already overlap with enforcement

&#x20; and provenance-aware defenses.

\- A defensible novelty claim requires a detailed comparison

&#x20; of their exact tasks, languages, policies, and metrics.

\- If an adequate model or reproducible agent environment is

&#x20; unavailable, reduce the scope rather than invent results.



\## Decision gate

Before implementation, determine whether the proposed

language-conditioned action-level evaluation fills a meaningful

gap not adequately covered by existing work.



If not, refine the question or reposition AEGIS as an

engineering and evaluation product rather than claiming a

novel research method.



\## Status

Preliminary assessment recorded.

Detailed paper, dataset, implementation, and license review

still required.



