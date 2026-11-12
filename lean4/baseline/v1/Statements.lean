-- Evaluator-owned statements. Inserted verbatim into challenge and solution.
theorem exact_grant (b : Nat) (a : Amount) :
    (admission b a).success = true → a = .nonneg (admission b a).granted := by
  PROOF_EXACT
theorem conservation (b : Nat) (a : Amount) :
    (admission b a).balance + (admission b a).granted = b := by
  PROOF_CONSERVATION
theorem failure_preservation (b : Nat) (a : Amount) :
    (¬ positive a ∨ ¬ affordable a b) → admission b a = ⟨false, 0, b⟩ := by
  PROOF_FAILURE
theorem total_success (b : Nat) (a : Amount) :
    positive a → affordable a b → (admission b a).success = true := by
  PROOF_SUCCESS
