import Std
namespace ProofGate
/-- Nonneg n denotes n; neg p denotes -(p+1). Unbounded mathematical domain. -/
inductive Amount where
  | nonneg : Nat → Amount
  | neg : Nat → Amount
  deriving DecidableEq, Repr
structure Response where
  success : Bool
  granted : Nat
  balance : Nat
  deriving DecidableEq, Repr
def positive : Amount → Prop
  | .nonneg n => 0 < n
  | .neg _ => False
def affordable : Amount → Nat → Prop
  | .nonneg n, b => n ≤ b
  | .neg _, _ => True
end ProofGate
