import Base
import ./Model.bend as M

# Lift a decision after removing one unit from both inputs.
def lift(r: M.Response) -> M.Response:
  match r:
    case M.Response{False{}, g, b}:
      M.Response{False{}, g, 1n+b}
    case M.Response{True{}, g, b}:
      M.Response{True{}, 1n+g, b}

# Internal subtraction worker accepts zero. Public admission rejects zero.
def take(b: Nat, n: Nat) -> M.Response:
  match b n:
    case 0n 0n:
      M.Response{True{}, 0n, 0n}
    case 0n 1n+p:
      M.Response{False{}, 0n, 0n}
    case 1n+bp 0n:
      M.Response{True{}, 0n, 1n+bp}
    case 1n+bp 1n+np:
      lift(take(bp, np))

def admission(+b: Nat, a: M.Amount) -> M.Response:
  M.Response{False{}, 0n, b}
