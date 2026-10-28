import Base
import ./Model.bend as M
import ./Admission.bend as C
import ./LAWS.bend as L

# Boolean constructor discrimination, without an axiom.
def true_type(b: Bool) -> Type:
  match b:
    case False{}:
      Empty
    case True{}:
      Unit

def false_true(e: {False{} == True{} : Bool}) -> Empty:
  %Equal.sym(Bool, False{}, True{}, e) : true_type(_)
  Unit{}

def add_zero(+n: Nat) -> {Nat.add(n, 0n) == n : Nat}:
  match n:
    case 0n:
      {==}
    case 1n+p:
      %add_zero(p) : {1n+Nat.add(p, 0n) == 1n+_ : Nat}
      {==}

def add_succ(+a: Nat, +b: Nat) -> {Nat.add(a, 1n+b) == 1n+Nat.add(a, b) : Nat}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      %add_succ(p, b) : {1n+Nat.add(p, 1n+b) == 1n+_ : Nat}
      {==}

def lift_exact(+n: Nat, +r: M.Response, p: M.natural_exact(n, r)) -> M.natural_exact(1n+n, C.lift(r)):
  match r:
    case M.Response{False{}, g, b}:
      Unit{}
    case M.Response{True{}, g, b}:
      %p : {1n+g == 1n+_ : Nat}
      {==}

def take_exact(+b: Nat, +n: Nat) -> M.natural_exact(n, C.take(b, n)):
  match b n:
    case 0n 0n:
      {==}
    case 0n 1n+p:
      Unit{}
    case 1n+bp 0n:
      {==}
    case 1n+bp 1n+np:
      lift_exact(np, C.take(bp, np), take_exact(bp, np))

def lift_conserved(+b: Nat, +r: M.Response, p: M.conserved(b, r)) -> M.conserved(1n+b, C.lift(r)):
  match r:
    case M.Response{False{}, g, next}:
      %p : {1n+Nat.add(next, g) == 1n+_ : Nat}
      {==}
    case M.Response{True{}, g, next}:
      %Equal.sym(Nat, Nat.add(next, 1n+g), 1n+Nat.add(next, g), add_succ(next, g)) : {_ == 1n+b : Nat}
      %p : {1n+Nat.add(next, g) == 1n+_ : Nat}
      {==}

def take_conserved(+b: Nat, +n: Nat) -> M.conserved(b, C.take(b, n)):
  match b n:
    case 0n 0n:
      {==}
    case 0n 1n+p:
      {==}
    case 1n+bp 0n:
      add_zero(1n+bp)
    case 1n+bp 1n+np:
      lift_conserved(bp, C.take(bp, np), take_conserved(bp, np))

# Mathematical non-affordability, independent of C.take.
def take_failure(+b: Nat, +n: Nat, e: {Bool.not(Nat.is_le(n, b)) == True{} : Bool}) -> {C.take(b, n) == M.Response{False{}, 0n, b} : M.Response}:
  match b n:
    case 0n 0n:
      Empty.absurd({C.take(0n, 0n) == M.Response{False{}, 0n, 0n} : M.Response}, false_true(e))
    case 0n 1n+p:
      {==}
    case 1n+bp 0n:
      Empty.absurd({C.take(1n+bp, 0n) == M.Response{False{}, 0n, 1n+bp} : M.Response}, false_true(e))
    case 1n+bp 1n+np:
      %take_failure(bp, np, e) : {C.lift(C.take(bp, np)) == C.lift(_) : M.Response}
      {==}

def lift_success(+r: M.Response, e: {M.success(r) == True{} : Bool}) -> {M.success(C.lift(r)) == True{} : Bool}:
  match r:
    case M.Response{False{}, g, b}:
      Empty.absurd({M.success(C.lift(M.Response{False{}, g, b})) == True{} : Bool}, false_true(e))
    case M.Response{True{}, g, b}:
      {==}

def take_success(+b: Nat, +n: Nat, e: {Nat.is_le(n, b) == True{} : Bool}) -> {M.success(C.take(b, n)) == True{} : Bool}:
  match b n:
    case 0n 0n:
      {==}
    case 0n 1n+p:
      Empty.absurd({M.success(C.take(0n, 1n+p)) == True{} : Bool}, false_true(e))
    case 1n+bp 0n:
      {==}
    case 1n+bp 1n+np:
      lift_success(C.take(bp, np), take_success(bp, np, e))

def signed_exact(+n: Nat, +r: M.Response, e: M.natural_exact(n, r)) -> M.exact(M.Nonneg{n}, r):
  match r:
    case M.Response{False{}, g, b}:
      Unit{}
    case M.Response{True{}, g, b}:
      %e : {M.Nonneg{g} == M.Nonneg{_} : M.Amount}
      {==}

def L.exact_grant(b, a):
  Unit{}

def L.conservation(b, a):
  add_zero(b)

def L.failure_preservation(b, a, invalid):
  {==}

def L.total_success(b, a, positive, affordable):
  match a:
    case M.Nonneg{0n}:
      Empty.absurd({M.success(C.admission(b, M.Nonneg{0n})) == True{} : Bool}, false_true(positive))
    case M.Nonneg{1n+p}:
      take_success(b, 1n+p, affordable)
    case M.Neg{p}:
      Empty.absurd({M.success(C.admission(b, M.Neg{p})) == True{} : Bool}, false_true(positive))
