

\# BhashaFence — Final MVP Scope



\## Product

BhashaFence: Cross-Lingual AI Agent Security Evaluation Lab



\## Repository

E:\\AEGIS



\## Goal

Build a reproducible security evaluation application that

compares how defense configurations handle controlled indirect

prompt-injection scenarios and whether prohibited tool actions

are actually executed.



\## MVP components

1\. Synthetic agent with simulated tools.

2\. Benign and adversarial scenario library.

3\. No-defense baseline.

4\. Rules-based content-filtering defense.

5\. Deterministic tool-authorization defense.

6\. Structured decision and execution logs.

7\. Evaluation metrics and results export.

8\. Automated security and regression tests.



\## Research experiment

Evaluate matched scenarios in English, Hindi, Marathi,

and code-mixed text, subject to validation of semantic equivalence.



Measure:

\- Unauthorized tool-action rate

\- Attack success rate

\- Legitimate task completion

\- False-positive block rate

\- Execution overhead



\## Safety boundaries

\- Synthetic data only in the initial implementation.

\- No real email, financial, or personal accounts.

\- No arbitrary filesystem or shell access for the simulated agent.

\- All tool actions pass through the controlled execution layer.

\- Untrusted content never supplies executable application code.



\## Research integrity

\- Do not claim a novel firewall or first multilingual benchmark.

\- Document competing work and licensing.

\- Report limitations and negative results.

\- Distinguish simulator results from real LLM evaluation.

\- Do not claim LLM robustness without testing an actual model.



\## Six-week priority

First deliver a correct and tested sandbox.

Then implement defenses and evaluation.

Build the dashboard after the evaluation pipeline works.



\## Completion criteria

\- Clean setup instructions.

\- Automated tests pass.

\- Unauthorized actions are blocked at the execution boundary.

\- Benign and adversarial cases are scored correctly.

\- Results are reproducible and exportable.

\- Limitations and research comparisons are documented.



\## Status

MVP scope frozen provisionally.

Implementation not yet started.



