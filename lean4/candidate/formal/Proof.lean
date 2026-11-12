import Admission
namespace ProofGate
theorem exact_grant (b : Nat) (a : Amount) :
    (admission b a).success = true → a = .nonneg (admission b a).granted := by
  cases a with
  | nonneg n => simp only [admission]; split <;> simp_all
  | neg p => simp [admission]
theorem conservation (b : Nat) (a : Amount) :
    (admission b a).balance + (admission b a).granted = b := by
  cases a with
  | nonneg n => simp only [admission]; split <;> simp_all <;> omega
  | neg p => simp [admission]
theorem failure_preservation (b : Nat) (a : Amount) :
    (¬ positive a ∨ ¬ affordable a b) → admission b a = ⟨false, 0, b⟩ := by
  cases a with
  | nonneg n => simp only [positive, affordable, admission]; split <;> simp_all
  | neg p => simp [admission]
theorem total_success (b : Nat) (a : Amount) :
    positive a → affordable a b → (admission b a).success = true := by
  cases a with
  | nonneg n => simp_all [positive, affordable, admission]
  | neg p => simp [positive]
end ProofGate
