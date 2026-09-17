---

description: "Task list for feature implementation"

---

# Tasks: Baixar Boletins do SIGAA (IFFar)

**Input**: Design documents from `specs/001-baixar-boletins-sigaa/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification, so no dedicated test tasks are included. (Pure-logic modules `input_csv.py` and `report.py` are isolated for easy unit testing later if desired.)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Single project: `src/`, `tests/` at repository root (per plan.md)
- Package: `src/baixar_boletins/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create `requirements.txt` listing the Playwright dependency (pinned) for Python 3.12
- [X] T002 [P] Create package marker `src/baixar_boletins/__init__.py` and the `src/baixar_boletins/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Implement CSV input reading/validation in `src/baixar_boletins/input_csv.py`: read column `Matricula`, trim whitespace, drop empty/duplicate rows, raise clear error if column missing or file empty (per contracts/cli.md and FR-001)
- [X] T004 [P] Implement execution report/state in `src/baixar_boletins/report.py`: per-matricula status (`pendente`, `sucesso`, `nao_encontrada`, `erro`, `invalida`), load/save of `boletins/.progresso.json`, and final summary rendering (per data-model.md and FR-008/FR-009)
- [X] T005 Implement CLI entry point in `src/baixar_boletins/cli.py`: argument parsing (`caminho-do-csv`, `--pasta`, `--url`, `--reprocessar`, `--perfil`) and exit codes 0/1/2/3 (per contracts/cli.md)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Baixar boletins em lote a partir de um CSV (Priority: P1) 🎯 MVP

**Goal**: Lê o CSV, cria `boletins/`, navega no SIGAA até "Emitir Boletim" e, para cada matrícula, busca o discente e salva o boletim oficial em PDF (Paisagem, Escala 100) como `<matricula>.pdf`, emitindo relatório final.

**Independent Test**: Executar `python -m baixar_boletins T10.csv` e verificar que `boletins/` contém um PDF por matrícula encontrada, com o layout oficial do SIGAA, e que o relatório final lista sucessos/não encontradas.

### Implementation for User Story 1

- [X] T006 [US1] Implement persistent browser session bootstrap in `src/baixar_boletins/sigaa_nav.py`: launch persistent context from `--perfil`, detect authentication state, and pause for manual login when the session expired (per FR-010 and research.md)
- [X] T007 [US1] Implement navigation to "Emitir Boletim" in `src/baixar_boletins/sigaa_nav.py`: open `--url` and click through "Ensino Técnico Integrado > Documentos de Discentes > Emitir Boletim" to reach "Buscar Discente" (per FR-003)
- [X] T008 [US1] Implement per-matricula search in `src/baixar_boletins/sigaa_nav.py`: check "Matrícula", fill number (clearing previous value), trigger search, and select the matching discente ("Selecionar Discente") to open the Boletim Escolar (per FR-004/FR-005)
- [X] T009 [P] [US1] Implement PDF rendering in `src/baixar_boletins/pdf_render.py`: render the boletim from the SIGAA print view as PDF with landscape (`Paisagem`) and scale 1.0 (`Escala 100`), saving to `<pasta>/<matricula>.pdf` (per FR-006/FR-007 and research.md)
- [X] T010 [US1] Implement pacing and retry in the batch loop in `src/baixar_boletins/cli.py`: fixed 1–2s pause between matrículas (FR-011) and up to 3 automatic retries on transient network errors before marking `erro` and continuing (FR-012)
- [X] T011 [US1] Wire the end-to-end batch loop in `src/baixar_boletins/cli.py`: for each matrícula, search → select → render PDF → record status; then print the final report (successes, not-found, errors, output path)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Relatório de execução e retomada (Priority: P2)

**Goal**: Reexecutar o script sem baixar novamente os PDFs já obtidos, pulando matrículas concluídas e exibindo um resumo da execução.

**Independent Test**: Executar `python -m baixar_boletins T10.csv` duas vezes seguidas e confirmar que a segunda execução pula as matrículas já baixadas (sem duplicar) e exibe o resumo; `--reprocessar` força a reescrita.

### Implementation for User Story 2

- [X] T012 [US2] Implement idempotent resume in `src/baixar_boletins/report.py` and `src/baixar_boletins/cli.py`: on re-run, skip matrículas already in `sucesso`/`nao_encontrada`/`invalida` (reprocess only `pendente`/`erro`), per data-model.md and SC-004
- [X] T013 [US2] Implement `--reprocessar` option and re-run summary in `src/baixar_boletins/cli.py`: force regeneration of all matrículas when the flag is present, and report existing vs. newly downloaded vs. skipped counts

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T014 Run the validation scenarios in `quickstart.md` end-to-end using `T10.csv` and confirm the results match expectations
- [X] T015 Harden user-facing error messages for invalid CSV, session timeout, and unexpected SIGAA menu changes (avoid silent failures, per FR-008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — builds on US1's report/state module but is independently testable

### Within Each User Story

- Foundational modules (`input_csv.py`, `report.py`) before `cli.py`
- `sigaa_nav.py` (bootstrap → navigation → search) in order, since they share the same file
- `pdf_render.py` is a separate file and can be written in parallel with `sigaa_nav.py`
- Core implementation before integration (T011 wires everything together)

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- T003 and T004 (Foundational) can run in parallel; T005 depends on both
- T009 (`pdf_render.py`) can run in parallel with T006–T008 (`sigaa_nav.py`)
- US1 and US2 can proceed in parallel by different developers after Foundational

---

## Parallel Example: User Story 1

```bash
# While sigaa_nav.py is being built (T006–T008), build the PDF renderer in parallel:
Task: "T009 Implement PDF rendering in src/baixar_boletins/pdf_render.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with `T10.csv`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently (re-run idempotency) → Demo
4. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests were not explicitly requested; the design keeps `input_csv.py` and `report.py` pure for easy unit testing later
