-- Cyclic trace invariance minimal case (theory case study, M15).
-- Real-tool evidence: this file is compiled by the real Lean 4 binary in the
-- case-study eval (run_lean); only an exit-0 run may be recorded as evidence.
--
-- Minimal analog of tr(AB)=tr(BA): rotating a 2-tuple preserves its sum.

def rot2 (p : Nat × Nat) : Nat × Nat := (p.2, p.1)

theorem rot2_preserves_sum (a b : Nat) : (rot2 (a, b)).1 + (rot2 (a, b)).2 = a + b := by
  simp [rot2, Nat.add_comm]
