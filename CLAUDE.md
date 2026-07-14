# CLAUDE.md — C2G AI Context

    > Session loader for AI work inside `c2g`.
    > Keep durable engineering rules in [`AGENTS.md`](AGENTS.md) and volatile facts in SSOT files.

    ## Load First

    1. [`AGENTS.md`](AGENTS.md)
    2. [`README.md`](README.md) when present
    3. The source files and tests directly related to the task
    4. Workspace context in [`../../CLAUDE.md`](../../CLAUDE.md) when the task crosses project boundaries
    5. System index in [`../../docs/SYSTEM-INDEX.md`](../../docs/SYSTEM-INDEX.md) for workspace navigation
    5. System index in [`../../docs/SYSTEM-INDEX.md`](../../docs/SYSTEM-INDEX.md) for workspace navigation

    ## Project Role

    - Layer: X
    - Responsibility: 战略需求引擎：Concept/Pitch/Bet 到治理任务
    - Stack: Python / uv

    ## Commands

    ```bash
    uv sync
uv run pytest "tests/" -q
uv run ruff check "src/"
    ```

    ## Safe Editing Rules

    - `向 .omo 物化任务必须走 c2g/omo broker，禁止手写 planned task。`
- Pitch frontmatter 是契约，改格式要同步解析器和测试。

    - Do not commit, push, reset, or bump submodule pointers unless the user explicitly asks.
    - Preserve unrelated dirty changes in this repository.
    - Keep Markdown pointed at SSOT files instead of copying generated facts.

    ## Closeout

    ```bash
    git status --short
    uv run --with "pyyaml" python "../../bin/doc-ssot-lint.py" --json
    ```

    Report the checks you actually ran and any pre-existing dirty state that remains.
