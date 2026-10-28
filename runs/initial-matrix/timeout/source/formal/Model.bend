import Base

# Semantic model: Nonneg(m) denotes m; Neg(p) denotes -(p+1).
type Amount is Data:
  Nonneg{magnitude: Nat}
  Neg{pred: Nat}

type Response is Data:
  Response{success: Bool, granted: Nat, balance: Nat}

def success(r: Response) -> Bool:
  match r:
    case Response{s, g, b}:
      s

def granted(r: Response) -> Nat:
  match r:
    case Response{s, g, b}:
      g

def balance(r: Response) -> Nat:
  match r:
    case Response{s, g, b}:
      b

# Independent mathematical predicates, not admission decision helpers.
def positive(a: Amount) -> Bool:
  match a:
    case Nonneg{0n}:
      False{}
    case Nonneg{1n+p}:
      True{}
    case Neg{p}:
      False{}

def affordable(a: Amount, b: Nat) -> Bool:
  match a:
    case Nonneg{n}:
      Nat.is_le(n, b)
    case Neg{p}:
      True{}

def invalid(+a: Amount, b: Nat) -> Bool:
  Bool.or(Bool.not(positive(a)), Bool.not(affordable(a, b)))

def exact(a: Amount, r: Response) -> Type:
  match r:
    case Response{False{}, g, b}:
      Unit
    case Response{True{}, g, b}:
      {Nonneg{g} == a : Amount}

def natural_exact(n: Nat, r: Response) -> Type:
  match r:
    case Response{False{}, g, b}:
      Unit
    case Response{True{}, g, b}:
      {g == n : Nat}

def conserved(b: Nat, r: Response) -> Type:
  match r:
    case Response{s, g, next}:
      {Nat.add(next, g) == b : Nat}
