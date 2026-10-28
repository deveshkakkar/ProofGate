import Base
import ./Model.bend as M
import ./Admission.bend as C

law exact_grant:
  for +b: Nat
  for +a: M.Amount
  M.exact(a, C.admission(b, a))

law conservation:
  for +b: Nat
  for +a: M.Amount
  M.conserved(b, C.admission(b, a))

law failure_preservation:
  for +b: Nat
  for +a: M.Amount
  for invalid: {M.invalid(a, b) == True{} : Bool}
  {C.admission(b, a) == M.Response{False{}, 0n, b} : M.Response}

law total_success:
  for +b: Nat
  for +a: M.Amount
  for positive: {M.positive(a) == True{} : Bool}
  for affordable: {M.affordable(a, b) == True{} : Bool}
  {M.success(C.admission(b, a)) == True{} : Bool}
