import Admission
open ProofGate
/-- Protected line protocol: batch of balance/signed amount pairs in; triples out.
    The pure core retains the unbounded domain; this adapter enforces service bounds. -/
def main : IO UInt32 := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  repeat
    let line ← stdin.getLine
    if line.isEmpty then break
    let parts := line.trimAscii.toString.splitOn " "
    match parts with
    | [bs, as] =>
      match bs.toNat?, as.toInt? with
      | some b, some a =>
        if b > 100 || a.natAbs > 281474976710655 then return 2
        let amount := if a < 0 then Amount.neg (a.natAbs - 1) else Amount.nonneg a.natAbs
        let r := admission b amount
        stdout.putStrLn s!"{if r.success then 1 else 0} {r.granted} {r.balance}"
      | _, _ => return 2
    | _ => return 2
  return 0
