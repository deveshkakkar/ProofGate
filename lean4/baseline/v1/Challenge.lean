import Admission
namespace ProofGate
-- Evaluator-owned statements. Inserted verbatim into challenge and solution.
theorem exact_grant (b : Nat) (a : Amount) :
    (admission b a).success = true → a = .nonneg (admission b a).granted := by
  sorry
theorem conservation (b : Nat) (a : Amount) :
    (admission b a).balance + (admission b a).granted = b := by
  sorry
theorem failure_preservation (b : Nat) (a : Amount) :
    (¬ positive a ∨ ¬ affordable a b) → admission b a = ⟨false, 0, b⟩ := by
  sorry
theorem total_success (b : Nat) (a : Amount) :
    positive a → affordable a b → (admission b a).success = true := by
  sorry
end ProofGate
