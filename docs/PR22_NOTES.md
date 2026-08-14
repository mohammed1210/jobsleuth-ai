# Evidence Matching v2 validation notes

This implementation upgrades vacancy analysis from word overlap to structured, explainable evidence support.

Key invariants:
- shared wording alone must not create a strong match;
- deterministic strong matches require recorded personal actions and an outcome;
- semantic assessments are optional and fall back safely;
- semantic supporting facts must be grounded in the saved Evidence Card;
- essential partial/weak/missing support leads to CONSIDER unless an explicit blocker with weak/missing support requires SKIP;
- trainable requirements remain separate from existing-evidence assessment;
- no candidate data is committed to the repository.
