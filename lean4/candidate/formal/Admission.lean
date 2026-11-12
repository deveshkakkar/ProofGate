import Model
namespace ProofGate
def admission (b : Nat) (a : Amount) : Response :=
  match a with
  | .nonneg n => if 0 < n ∧ n ≤ b then ⟨true, n, b - n⟩ else ⟨false, 0, b⟩
  | .neg _ => ⟨false, 0, b⟩
end ProofGate
