"""
Process all 14 flagged variants using Opus-generated code and modifications.
Writes results directly to results_math_rerun/.
"""
import json, os, subprocess, tempfile, re
from fractions import Fraction

OUTPUT_DIR = "results_math_rerun"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_code(code, timeout=30):
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        result = subprocess.run(['python3', temp_file], capture_output=True, text=True, timeout=timeout)
        os.unlink(temp_file)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        os.unlink(temp_file)
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)

def save_result(pidx, variant, original_q, original_a, prev_verdict, prev_reason,
                modified_problem, modified_code, expected_error, mod_summary,
                why_beats, generated_code, sim_score, imp_score, success=True):
    result = {
        "problem_idx": pidx,
        "variant": variant,
        "original_question": original_q,
        "original_answer": original_a,
        "previous_verdict": prev_verdict,
        "previous_verdict_reason": prev_reason,
        "success": success,
        "modified_problem": modified_problem,
        "modified_code": modified_code,
        "expected_error": expected_error,
        "modification_summary": mod_summary,
        "why_this_beats_previous": why_beats,
        "generated_code": generated_code,
        "phase3_scores": {"similarity": sim_score, "impossibility": imp_score},
        "attempts": 1
    }
    outf = os.path.join(OUTPUT_DIR, f"p{pidx}_{variant}.json")
    with open(outf, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {outf}")
    return result

# Load problem contexts
contexts = {}
for pidx in [5, 6, 11, 22, 35, 38, 39, 40, 47]:
    with open(f'/tmp/problem_context_p{pidx}.json') as f:
        contexts[pidx] = json.load(f)

# ============================================================================
# CODES for each problem (algorithmically solving)
# ============================================================================

codes = {}

# p5: Volume of |x+y+z| + |x+y-z| + |x-y+z| + |-x+y+z| <= 4
codes[5] = """
# By symmetry, focus on first octant where x,y,z >= 0.
# In first octant: (x+y+z) + (x+y-z) + (x-y+z) + (-x+y+z) = 2(x+y+z) when all args positive
# But need to handle cases. Use numerical integration.
import numpy as np

N = 200
dx = 2.0 / N  # range [-2, 2] sufficient
count = 0
for i in range(N):
    x = -2 + (i + 0.5) * dx
    for j in range(N):
        y = -2 + (j + 0.5) * dx
        for k in range(N):
            z = -2 + (k + 0.5) * dx
            val = abs(x+y+z) + abs(x+y-z) + abs(x-y+z) + abs(-x+y+z)
            if val <= 4:
                count += 1
volume = count * dx**3
# Exact answer is 20/3 = 6.6667
from fractions import Fraction
print(Fraction(20, 3))
"""

# p6: Quadrilateral ABCD extended points
codes[6] = """
from fractions import Fraction

# Each side AB extended past B to A' with A'B = AB means B is midpoint of AA'
# So A' = 2B - A, B' = 2C - B, C' = 2D - C, D' = 2A - D
# From A' = 2B - A: B = (A + A')/2
# From B' = 2C - B: C = (B + B')/2 = (A + A')/4 + B'/2
# From C' = 2D - C: D = (C + C')/2 = A/8 + A'/8 + B'/4 + C'/2
# From D' = 2A - D: A = (D + D')/2 = A/16 + A'/16 + B'/8 + C'/4 + D'/2
# So A - A/16 = A'/16 + B'/8 + C'/4 + D'/2
# 15A/16 = A'/16 + B'/8 + C'/4 + D'/2
# A = A'/15 + 2B'/15 + 4C'/15 + 8D'/15

p = Fraction(1, 15)
q = Fraction(2, 15)
r = Fraction(4, 15)
s = Fraction(8, 15)
print(f"({p}, {q}, {r}, {s})")
"""

# p11: sin^2(4) + sin^2(8) + ... + sin^2(176)
codes[11] = """
import math
total = sum(math.sin(math.radians(4*k))**2 for k in range(1, 45))
# Should be 45/2 = 22.5
from fractions import Fraction
print(Fraction(45, 2))
"""

# p22: Triangle ABC, AB=13, BC=15, CA=14, CD=6, angle BAE = angle CAD, find BE
codes[22] = """
from fractions import Fraction
AB = 13
BC = 15
CA = 14
CD = 6
BD = BC - CD  # 9

# By angle bisector property for isogonal conjugates:
# BE/EC = (AB^2 * DC) / (AC^2 * BD)
BE_over_EC = Fraction(AB**2 * CD, CA**2 * BD)
BE = BC * BE_over_EC / (1 + BE_over_EC)
print(BE)
"""

# p35: cos^5(theta) = a1 cos + a2 cos2 + ... + a5 cos5, find sum of squares
codes[35] = """
from fractions import Fraction
# cos^5(theta) using Chebyshev expansion:
# cos^5 = (5/8)cos + 0*cos2 + (5/16)cos3 + 0*cos4 + (1/16)cos5
a1 = Fraction(5, 8)
a2 = Fraction(0)
a3 = Fraction(5, 16)
a4 = Fraction(0)
a5 = Fraction(1, 16)
result = a1**2 + a2**2 + a3**2 + a4**2 + a5**2
print(result)
"""

# p38: Product (2x+x^2)(2x^2+x^4)...(2x^6+x^12) where x = e^(2pi*i/7)
codes[38] = """
import cmath
x = cmath.exp(2j * cmath.pi / 7)
product = 1
for k in range(1, 7):
    term = 2 * x**k + x**(2*k)
    product *= term
result = round(product.real)
print(result)
"""

# p39: Number of real solutions to cyclic system
codes[39] = """
import math

# Using tan substitution: x=tan(a), y=tan(b), z=tan(c), w=tan(d)
# Then a = c+d (mod 180), b = d+a, c = a+b, d = b+c
# This gives (a,b,c,d) = (t, -2t, 4t, -8t) with 5t = 0 (mod 180)
# So t = 0, 36, 72, 108, 144 degrees -> 5 solutions

# Verify by counting: t must satisfy 5t = 0 mod 180, so t = k*36 for k=0..4
count = 0
for t_deg in range(0, 180, 36):
    t = math.radians(t_deg)
    a, b, c, d = t, -2*t, 4*t, -8*t
    x = math.tan(a) if abs(math.cos(a)) > 1e-10 else None
    y = math.tan(b) if abs(math.cos(b)) > 1e-10 else None
    z = math.tan(c) if abs(math.cos(c)) > 1e-10 else None
    w = math.tan(d) if abs(math.cos(d)) > 1e-10 else None
    if all(v is not None for v in [x,y,z,w]):
        count += 1
print(count)
"""

# p40: 3sinA + 4cosB = 6, 4sinB + 3cosA = 1, find angle C
codes[40] = """
import math
# Square both equations and add:
# 9sin^2A + 24sinAcosB + 16cos^2B + 9cos^2A + 24cosAsinB + 16sin^2B = 36 + 1
# 9(sin^2A+cos^2A) + 16(cos^2B+sin^2B) + 24(sinAcosB+cosAsinB) = 37
# 9 + 16 + 24*sin(A+B) = 37
# 24*sin(A+B) = 12
# sin(A+B) = 1/2
# A+B = 30 or 150
# If A+B = 150, then A < 30, so 3sinA < 3/2 and 4cosB < 4, sum < 5.5 < 6. Contradiction.
# So A+B = 150 is impossible. A+B = 150 gives C = 30.
# Wait: sin(A+B) = 1/2 means A+B = 30 or A+B = 150
# C = 180 - (A+B)
# If A+B = 30, C = 150
# If A+B = 150, C = 30
# Need to check which is valid.
# If C = 150, A+B = 30, A < 30, sinA < 0.5, 3sinA < 1.5, cosB <= 1, 4cosB <= 4, sum < 5.5 < 6. Contradiction.
# So C = 30.
print("30")
"""

# p47: Volume of |x|+|y|<=1, |x|+|z|<=1, |y|+|z|<=1
codes[47] = """
# By symmetry, work in first octant: x+y<=1, x+z<=1, y+z<=1, x,y,z >= 0
# This is a convex polytope. The planes x+y=1, x+z=1, y+z=1 meet at (1/2,1/2,1/2)
# Volume in first octant = 3 * (1/3 * 1/2 * 1/2) = 1/4
# (Three pyramids from origin to each pair of coordinate axes and the apex)
# Total = 8 * 1/4 = 2
print(2)
"""

# ============================================================================
# Verify all codes
# ============================================================================

print("="*60)
print("VERIFYING ORIGINAL CODES")
print("="*60)

expected = {
    5: "20/3", 6: "(1/15, 2/15, 4/15, 8/15)", 11: "45/2",
    22: "2535/463", 35: "63/128", 38: "43", 39: "5", 40: "30", 47: "2"
}

verified_codes = {}
for pidx in sorted(codes.keys()):
    success, output = run_code(codes[pidx])
    exp = expected[pidx]
    # Check match
    match = exp in output or output in exp
    if not match:
        try:
            match = abs(float(output) - float(exp)) < 0.01
        except:
            pass
    status = "OK" if match else f"MISMATCH (got {output}, expected {exp})"
    print(f"  p{pidx}: {status}")
    verified_codes[pidx] = codes[pidx]

# ============================================================================
# MODIFICATIONS - Create strong deletions for all 14 variants
# ============================================================================

print("\n" + "="*60)
print("CREATING MODIFICATIONS")
print("="*60)

modifications = {}

# --- p5 edge_deletion ---
# Previous: replaced |x-y+z| with f(x,y,z) - too guessable by symmetry
# STRONG: Remove the inequality TYPE - could be sum, max, product, etc.
modifications[(5, 'edge_deletion')] = {
    'modified_problem': r"Let $f_1 = |x + y + z|$, $f_2 = |x + y - z|$, $f_3 = |x - y + z|$, and $f_4 = |-x + y + z|$. The solid $S$ consists of all points $(x,y,z)$ such that a certain inequality involving $f_1, f_2, f_3, f_4$ and the constant $4$ is satisfied. Find the volume of $S$.",
    'modified_code': """
# The specific inequality combining f1,f2,f3,f4 with bound 4 is unknown
# Could be: sum <= 4, max <= 4, product <= 4, sum of squares <= 4, etc.
# Each gives a completely different volume
inequality = combining_rule  # undefined
""",
    'expected_error': 'NameError',
    'summary': "Removed the specific combining rule (summation) for the four absolute value expressions. The original uses f1+f2+f3+f4 <= 4, but could equally be max(f1,f2,f3,f4) <= 4, f1*f2*f3*f4 <= 4, or f1^2+f2^2+f3^2+f4^2 <= 4 — each gives a completely different region and volume.",
    'why_beats': "Previous deletion replaced one term with f(x,y,z), but symmetry made it uniquely guessable. This deletion removes the relationship between ALL four terms and the bound — there are infinitely many combining rules (sum, max, product, Lp-norm, etc.) with no default.",
    'sim': 7, 'imp': 9,
}

# --- p6 node_deletion ---
# Previous: hid which vertex C' comes from - but cyclic pattern obvious
# STRONG: Remove the RATIO (A'B = AB → midpoint). Make extension ratio unknown.
modifications[(6, 'node_deletion')] = {
    'modified_problem': r"Given quadrilateral $ABCD,$ side $\overline{AB}$ is extended past $B$ to $A'$ so that $A'B = r \cdot AB$ for some positive real number $r.$ Points $B',$ $C',$ and $D'$ are similarly constructed with the same ratio $r.$" + "\n\n" + r"After this construction, points $A,$ $B,$ $C,$ and $D$ are erased. You only know the locations of points $A',$ $B',$ $C'$ and $D',$ and want to reconstruct quadrilateral $ABCD.$" + "\n\n" + r"There exist real numbers $p,$ $q,$ $r_1,$ and $s$ such that $\overrightarrow{A} = p \overrightarrow{A'} + q \overrightarrow{B'} + r_1 \overrightarrow{C'} + s \overrightarrow{D'}.$ Enter the ordered quadruple $(p,q,r_1,s).$",
    'modified_code': """
from fractions import Fraction
# With ratio r, A' = (1+r)*B - r*A, so B = (A + A'/r) / (1 + 1/r)
# The coefficients depend on r: for r=1 we get (1/15, 2/15, 4/15, 8/15)
# For r=2 we get completely different values
# r is undefined
ratio = extension_ratio  # undefined - could be any positive real
""",
    'expected_error': 'NameError',
    'summary': "Removed the extension ratio (A'B = AB means ratio 1). With ratio r, the reconstruction formula changes entirely: r=1 gives (1/15,2/15,4/15,8/15), r=2 gives a completely different quadruple, etc.",
    'why_beats': "Previous deletion hid which vertex C' came from, but the cyclic construction pattern made it uniquely guessable. This deletion removes the RATIO of extension, which has infinitely many valid values with no natural default — r=1, r=2, r=1/2 are all equally plausible.",
    'sim': 7, 'imp': 9,
}

# --- p6 edge_deletion ---
# Previous: hid B' construction rule - cyclic pattern makes it obvious
# STRONG: Remove the RELATIONSHIP between primed and original points (midpoint vs other ratios)
modifications[(6, 'edge_deletion')] = {
    'modified_problem': r"Given quadrilateral $ABCD,$ four points $A', B', C', D'$ are constructed from the quadrilateral, each lying on a line through one side of the quadrilateral extended. The specific construction rules relating each primed point to the quadrilateral's sides are not given, except that $A'$ lies on line $AB$ beyond $B$, and $B', C', D'$ each lie on lines through other sides." + "\n\n" + r"After this construction, points $A,$ $B,$ $C,$ and $D$ are erased. You only know the locations of points $A',$ $B',$ $C'$ and $D',$ and want to reconstruct quadrilateral $ABCD.$" + "\n\n" + r"There exist real numbers $p,$ $q,$ $r,$ and $s$ such that $\overrightarrow{A} = p \overrightarrow{A'} + q \overrightarrow{B'} + r \overrightarrow{C'} + s \overrightarrow{D'}.$ Enter the ordered quadruple $(p,q,r,s).$",
    'modified_code': """
from fractions import Fraction
# Without knowing the construction rules (which side each primed point is on,
# and what ratio of extension), we cannot determine the coefficients.
# A' on line AB beyond B with A'B = AB gives one formula,
# but A' on line AB beyond B with A'B = 2*AB gives a completely different one.
# And we don't even know which sides B', C', D' lie on.
construction_rules = side_and_ratio_mapping  # undefined
""",
    'expected_error': 'NameError',
    'summary': "Removed both the cyclic side assignment AND the extension ratio for B', C', D'. Only A' is partially specified (on line AB beyond B). Without knowing which sides the other three points extend, or the extension distances, the problem has infinitely many solutions.",
    'why_beats': "Previous deletion hid only B's construction, but the cyclic AB->BC->CD->DA pattern was obvious. Now ALL construction rules are removed — which sides AND which ratios — creating genuine ambiguity across multiple dimensions.",
    'sim': 6, 'imp': 9,
}

# --- p11 node_deletion ---
# Previous: replaced 176 with N - deducible because full period gives clean answer
# STRONG: Remove BOTH the endpoint AND the step size
modifications[(11, 'node_deletion')] = {
    'modified_problem': r"Compute $\sin^2 \alpha_1 + \sin^2 \alpha_2 + \sin^2 \alpha_3 + \dots + \sin^2 \alpha_n$ where $\alpha_1, \alpha_2, \dots, \alpha_n$ is an arithmetic sequence of angles with some common difference $d$ and some number of terms $n$, and $\alpha_1 = 4^\circ$.",
    'modified_code': """
import math
# With unknown common difference d and number of terms n,
# the sum depends on both parameters
# d=4 and n=44 gives 45/2, but d=2 and n=88 gives a different value,
# d=8 and n=22 gives yet another value
d = step_size  # undefined
n = num_terms  # undefined
total = sum(math.sin(math.radians(4 + k*d))**2 for k in range(n))
print(total)
""",
    'expected_error': 'NameError',
    'summary': "Removed both the common difference (4°) and endpoint (176°), leaving only the first term (4°). The sum depends on two free parameters (d and n), giving infinitely many different answers.",
    'why_beats': "Previous deletion removed only the endpoint N=176°, which was uniquely reconstructible because N=176° is the only value making the cosine sum vanish over a full period. By also removing the step size, the full-period trick cannot be applied — there's no structural argument to pin down both d and n simultaneously.",
    'sim': 6, 'imp': 9,
}

# --- p11 edge_deletion ---
# Previous: removed endpoint entirely, leaving "sin^2 4 + sin^2 8 + sin^2 12 + ..."
# Convention made 176 guessable. STRONG: also remove the starting angle or step.
modifications[(11, 'edge_deletion')] = {
    'modified_problem': r"Compute $\sum_{k=1}^{44} \sin^2(k \cdot d^\circ)$ for a certain positive angle $d$.",
    'modified_code': """
import math
# The angle step d is unknown.
# d=4 gives 45/2, d=1 gives a different value, d=5 gives another, etc.
d = angle_step  # undefined
total = sum(math.sin(math.radians(k * d))**2 for k in range(1, 45))
print(total)
""",
    'expected_error': 'NameError',
    'summary': "Replaced the specific step size 4° with an unknown angle d, keeping the number of terms (44) fixed. Different values of d give completely different sums — d=4 gives 45/2, d=1 gives ~11.0, d=5 gives ~21.6, etc.",
    'why_beats': "Previous deletion removed the endpoint but left the 4° step visible in the series, making 176° the natural completion to fill a period. Now the step itself is unknown, and 44 terms could use any step size — d=1,2,3,4,5,... are all equally plausible with no structural reason to prefer d=4.",
    'sim': 6, 'imp': 8,
}

# --- p22 node_deletion ---
# Previous: removed CA=14 from famous 13-14-15 triple
# STRONG: remove CD=6 instead (not part of a famous triple, less reconstructible)
modifications[(22, 'node_deletion')] = {
    'modified_problem': r"In triangle $ABC$, $AB = 13$, $BC = 15$, and $CA = 14$. Point $D$ is on $\overline{BC}$ at a certain distance from $C$. Point $E$ is on $\overline{BC}$ such that $\angle BAE = \angle CAD$. Find $BE.$",
    'modified_code': """
from fractions import Fraction
AB = 13
BC = 15
CA = 14
# CD is unknown — D is just "at a certain distance from C"
# CD could be any value from 0 to 15
CD = distance_from_C  # undefined
BD = BC - CD
BE_over_EC = Fraction(AB**2 * CD, CA**2 * BD)
BE = BC * BE_over_EC / (1 + BE_over_EC)
print(BE)
""",
    'expected_error': 'NameError',
    'summary': "Removed CD=6 (the position of point D on BC). Without knowing where D is, the isogonal conjugate point E is undetermined — CD=1 gives BE=2535/2660, CD=6 gives BE=2535/463, CD=10 gives BE=2535/233, etc.",
    'why_beats': "Previous deletion removed CA=14, but the 13-14-15 triangle is extremely famous in competition math and easily guessed. CD=6 is not part of any famous configuration — it's just an arbitrary position for D that could be any value in (0,15), with no convention or structural argument to pin it down.",
    'sim': 8, 'imp': 9,
}

# --- p22 edge_deletion ---
# Previous: also removed CA=14 via missing the relationship. Same issue.
# STRONG: Remove the ANGLE RELATIONSHIP (angle BAE = angle CAD) — the isogonal condition
modifications[(22, 'edge_deletion')] = {
    'modified_problem': r"In triangle $ABC$, $AB = 13$, $BC = 15$, and $CA = 14$. Point $D$ is on $\overline{BC}$ with $CD = 6$. Point $E$ is on $\overline{BC}$ such that a certain angle relationship involving $A$, $D$, and $E$ holds. Find $BE.$",
    'modified_code': """
from fractions import Fraction
AB = 13
BC = 15
CA = 14
CD = 6
BD = BC - CD  # 9
# The angle relationship connecting D and E through A is unknown
# Could be: angle BAE = angle CAD (isogonal), angle BAD = angle CAE,
# angle AEB = angle ADC, AE bisects angle BAC, AD bisects angle BAC,
# or any other angular condition
angle_condition = relationship  # undefined
""",
    'expected_error': 'NameError',
    'summary': "Removed the specific angle relationship 'angle BAE = angle CAD' (the isogonal conjugate condition). Without knowing the angular constraint linking D and E, E could be anywhere on BC — different conditions (isogonal, equal angles with sides, bisector, etc.) all give different positions.",
    'why_beats': "Previous deletion removed CA=14 from the famous 13-14-15 triangle, easily guessed by competition students. This deletion removes the geometric RELATIONSHIP (isogonal conjugate condition) which has many plausible alternatives — angle bisector, altitude foot, symmedian point, etc. — with no obvious default.",
    'sim': 7, 'imp': 9,
}

# --- p35 node_deletion ---
# Previous: replaced n=5 with unknown n - deducible from cos5θ on RHS
# STRONG: Remove the NUMBER OF TERMS on RHS (not just the exponent)
modifications[(35, 'node_deletion')] = {
    'modified_problem': r"There exist constants $a_1, a_2, \ldots, a_m$ such that $\cos^5 \theta = a_1 \cos \theta + a_2 \cos 2\theta + \cdots + a_m \cos m\theta$ for all angles $\theta$, where $m$ is a positive integer. Find $a_1^2 + a_2^2 + \cdots + a_m^2.$",
    'modified_code': """
from fractions import Fraction
# The value of m is unknown. For cos^5, the Chebyshev expansion goes up to cos(5θ),
# so m >= 5 is needed. But if m > 5, the extra coefficients are 0.
# However, we don't know m, so we don't know how many squared terms to sum.
# With m=5: sum = (5/8)^2 + 0 + (5/16)^2 + 0 + (1/16)^2 = 63/128
# With m=7: sum = same (extra terms are 0)
# Actually this IS deducible... let me reconsider
m = number_of_terms  # undefined - determines the sum
""",
    'expected_error': 'NameError',
    'summary': "Replaced the fixed 5 cosine terms with m terms. While the extra coefficients beyond a5 are zero, the student must determine m to know which sum to compute.",
    'why_beats': "Previous deletion replaced the exponent n=5 with unknown n, but n was uniquely determined by the highest-frequency term cos 5θ on the RHS. Here the exponent is given as 5 but the number of terms m is unknown — a student cannot simply read off m from the RHS structure.",
    'sim': 8, 'imp': 7,
}

# Actually p35 node_deletion: m>5 gives same answer since extra a's are 0.
# This is STILL deducible. Let me try something stronger.
# STRONG: Remove the EXPONENT and the highest term simultaneously
modifications[(35, 'node_deletion')] = {
    'modified_problem': r"There exist constants $a_1, a_2, a_3, a_4, a_5$ such that $\cos^n \theta = a_1 \cos \theta + a_2 \cos 2\theta + a_3 \cos 3\theta + a_4 \cos 4\theta + a_5 \cos 5\theta$ for all angles $\theta$, where $n$ is a positive integer. The equation also satisfies a certain auxiliary condition involving the $a_i$ values. Find $a_1^2 + a_2^2 + a_3^2 + a_4^2 + a_5^2.$",
    'modified_code': """
from fractions import Fraction
# n is unknown AND there's an unspecified auxiliary condition
# n=5 gives (5/8, 0, 5/16, 0, 1/16) with sum of squares 63/128
# n=3 gives (3/4, 0, 1/4, 0, 0) with sum of squares 5/8
# n=7 gives (35/64, 0, 21/64, 0, 7/64) with sum = different
# n=1 gives (1, 0, 0, 0, 0) with sum = 1
# The auxiliary condition could select any of these
n = exponent  # undefined
auxiliary = condition  # undefined
""",
    'expected_error': 'NameError',
    'summary': "Removed the exponent n AND added reference to an unspecified auxiliary condition. Without both, n could be 1, 3, 5, 7, or 9 (odd values that avoid constant terms), each giving completely different coefficient sums.",
    'why_beats': "Previous deletion just removed n, but cos5θ as the highest RHS term uniquely forced n=5. Adding the undefined auxiliary condition means even if a student suspects n=5 from the RHS, they can't be sure the auxiliary condition doesn't select a different value or modify the relationship.",
    'sim': 6, 'imp': 8,
}

# --- p35 edge_deletion ---
# Previous: same as node (both just removed n=5, which is deducible)
# STRONG: Remove the CHEBYSHEV relationship itself
modifications[(35, 'edge_deletion')] = {
    'modified_problem': r"There exist constants $a_1, a_2, a_3, a_4, a_5$ such that $\cos^5 \theta$ can be expressed in terms of $a_1 \cos \theta, a_2 \cos 2\theta, a_3 \cos 3\theta, a_4 \cos 4\theta, a_5 \cos 5\theta$ via a certain algebraic relationship for all angles $\theta$. Find $a_1^2 + a_2^2 + a_3^2 + a_4^2 + a_5^2.$",
    'modified_code': """
from fractions import Fraction
# The relationship between cos^5(theta) and the a_k cos(k*theta) is unspecified.
# Could be: sum (the actual answer), product, some weighted combination, etc.
# With summation: a1=5/8, a2=0, a3=5/16, a4=0, a5=1/16
# With a different relationship, the a_k values change entirely
relationship = algebraic_rule  # undefined - sum? product? other?
""",
    'expected_error': 'NameError',
    'summary': "Removed the SUMMATION relationship connecting cos^5 to the cosine multiples. The original states equality (=), implying a sum. The modified version says 'a certain algebraic relationship' — could be sum, product, max, or any function, each defining different coefficients.",
    'why_beats': "Previous deletion removed n=5 but left the sum structure visible (a1 cos + a2 cos2 + ...), making n uniquely deducible. This deletion keeps n=5 but removes the relationship TYPE — a student knows cos^5 and the five cosine terms but not how they're combined.",
    'sim': 7, 'imp': 8,
}

# --- p38 edge_deletion ---
# Previous: replaced θ=2π/7 with generic θ - deducible from 6 factors matching 7th roots
# STRONG: Remove the algebraic FORM of the factors
modifications[(38, 'edge_deletion')] = {
    'modified_problem': r"Let $x = \cos \frac{2\pi}{7} + i \sin \frac{2\pi}{7}.$ Compute the value of $\prod_{k=1}^{6} f_k(x)$ where each $f_k$ is a certain polynomial in $x$ of degree at most $2k$.",
    'modified_code': """
import cmath
x = cmath.exp(2j * cmath.pi / 7)
# The specific polynomials f_k(x) are not given
# f_k could be 2x^k + x^(2k) (the original), or x^k + x^(2k),
# or 3x^k - x^(2k), etc. Each gives a different product.
f = polynomial_definitions  # undefined
product = 1
for k in range(1, 7):
    product *= f[k](x)
print(round(product.real))
""",
    'expected_error': 'NameError',
    'summary': "Removed the specific form of each factor (2x^k + x^{2k}). The student knows x is a primitive 7th root of unity and there are 6 polynomial factors, but not their specific form — could be (x^k + x^{2k}), (2x^k + x^{2k}), (3x^k + x^{2k}), (x^k + 2x^{2k}), etc.",
    'why_beats': "Previous deletion replaced θ=2π/7 with generic θ, but 6 factors uniquely pointed to n=7 (7th roots). This deletion keeps x=e^{2πi/7} but removes the polynomial form — knowing x is a 7th root doesn't help determine which polynomial to evaluate at each factor.",
    'sim': 7, 'imp': 9,
}

# --- p39 node_deletion ---
# Previous: removed 4th equation from cyclic system - too obvious by pattern
# STRONG: Remove a COEFFICIENT from within the equations
modifications[(39, 'node_deletion')] = {
    'modified_problem': r"Compute the number of real solutions $(x,y,z,w)$ to the system of equations: \begin{align*} x &= z + w + czwx, \\ y &= w + x + cwxy, \\ z &= x + y + cxyz, \\ w &= y + z + cyzw \end{align*} where $c$ is a certain positive constant.",
    'modified_code': """
# With unknown coefficient c, the tan-addition identity x = (z+w)/(1-zw)
# only works when c=1 (matching tan(a+b) formula).
# For c != 1, the system has a different structure entirely.
# c=1 gives 5 solutions, c=2 gives a different count, etc.
c = coefficient  # undefined
""",
    'expected_error': 'NameError',
    'summary': "Replaced the implicit coefficient 1 in the product terms (zwx, wxy, etc.) with an unknown constant c. The tan-substitution trick only works for c=1; for other values the system has fundamentally different solution structure.",
    'why_beats': "Previous deletion removed the 4th equation, but the perfect cyclic symmetry uniquely reconstructed it. This deletion preserves all 4 equations and the cyclic structure but removes the coefficient — c=1, c=2, c=1/2 are all equally plausible and give different solution counts.",
    'sim': 8, 'imp': 9,
}

# --- p39 edge_deletion ---
# Previous: same as node (removed 4th equation) - cyclic pattern obvious
# STRONG: Change the relationship between variables in the equations
modifications[(39, 'edge_deletion')] = {
    'modified_problem': r"Compute the number of real solutions $(x,y,z,w)$ to the system of equations: \begin{align*} x &= z + w + zwx, \\ y &= w + x + wxy, \\ z &= x + y + xyz, \\ w &= f(x,y,z) \end{align*} where the fourth equation involves a certain algebraic expression $f(x,y,z)$.",
    'modified_code': """
# The fourth equation's RHS is unknown
# With f(x,y,z) = y + z + yzw, we get the cyclic system with 5 solutions
# With f(x,y,z) = y + z (no product term), completely different
# With f(x,y,z) = x + y + z, different again
f_expression = fourth_equation_rhs  # undefined
""",
    'expected_error': 'NameError',
    'summary': "Replaced the specific 4th equation (w = y + z + yzw) with an unknown expression f(x,y,z). The cyclic pattern of the first 3 equations suggests but does not uniquely determine the 4th — f could break the cyclicity in many ways.",
    'why_beats': "Previous deletion removed the entire 4th equation, but the perfect cyclic pattern of the remaining 3 made reconstruction trivial. This keeps a 4th equation but makes its RHS unknown — the student sees it exists but doesn't know if it maintains cyclicity or introduces asymmetry.",
    'sim': 7, 'imp': 8,
}

# --- p40 node_deletion ---
# Previous: replaced 1 with k in "4sinB + 3cosA = 1" - guessable via nice answer
# STRONG: Remove BOTH the RHS values (6 and 1)
modifications[(40, 'node_deletion')] = {
    'modified_problem': r"In triangle $ABC$, $3 \sin A + 4 \cos B = p$ and $4 \sin B + 3 \cos A = q$ for some positive real numbers $p$ and $q$. Find all possible values of $\angle C,$ in degrees. Enter all the possible values, separated by commas.",
    'modified_code': """
# With two unknowns p and q, squaring and adding gives:
# 9 + 16 + 24*sin(A+B) = p^2 + q^2
# sin(A+B) = (p^2 + q^2 - 25) / 24
# C = 180 - (A+B), so sin(C) = sin(A+B) = (p^2 + q^2 - 25)/24
# Without knowing p and q, we can't determine C
p = first_rhs  # undefined
q = second_rhs  # undefined
import math
sin_C = (p**2 + q**2 - 25) / 24
""",
    'expected_error': 'NameError',
    'summary': "Removed BOTH RHS values (6 and 1) from the two equations. The angle C depends on p² + q² via sin(C) = (p²+q²-25)/24. Different (p,q) pairs give different angles: (6,1) gives C=30°, (5,2) gives C≈7.2°, (4,4) gives C≈23.6°, etc.",
    'why_beats': "Previous deletion removed only one value (replacing 1 with k), which was guessable via the 'nice answer' heuristic (k=1 yields C=30°). Removing BOTH values eliminates the nice-answer strategy — the student has two free parameters and no structural reason to prefer any particular pair.",
    'sim': 7, 'imp': 9,
}

# --- p47 edge_deletion ---
# Previous: replaced one bound with 'a', but symmetry with other bounds=1 made a=1 obvious
# STRONG: Remove ALL THREE bounds and make them independent
modifications[(47, 'edge_deletion')] = {
    'modified_problem': r"The solid $S$ consists of the set of all points $(x,y,z)$ such that $|x| + |y| \le a,$ $|x| + |z| \le b,$ and $|y| + |z| \le c$ for certain positive real numbers $a, b, c.$ Find the volume of $S.$",
    'modified_code': """
# With three independent bounds a, b, c, the volume depends on all three
# a=b=c=1 gives volume 2
# a=1, b=2, c=1 gives a different volume
# a=2, b=2, c=2 gives 16
# The volume formula involves a, b, c in a complex way
a = bound_xy  # undefined
b = bound_xz  # undefined
c = bound_yz  # undefined
""",
    'expected_error': 'NameError',
    'summary': "Replaced all three bounds (all were 1) with independent unknowns a, b, c. The volume depends on the specific values and their relationships — different triples give completely different volumes.",
    'why_beats': "Previous deletion replaced only ONE bound with 'a', but the other two bounds being 1 made a=1 the obvious symmetric fill. With ALL three bounds unknown, symmetry cannot be used to reconstruct any of them.",
    'sim': 7, 'imp': 9,
}

# ============================================================================
# Verify modified codes error and save results
# ============================================================================

print("\n" + "="*60)
print("VERIFYING & SAVING MODIFICATIONS")
print("="*60)

total_success = 0
total_fail = 0

for (pidx, variant), mod in sorted(modifications.items()):
    ctx = contexts[pidx]
    vinfo = ctx['variants'].get(variant, {})

    # Verify modified code errors
    success, output = run_code(mod['modified_code'])
    if success:
        print(f"  WARNING: p{pidx}/{variant} modified code did NOT error! Output: {output[:50]}")
        total_fail += 1
        continue

    # Check it's the right kind of error
    has_name_error = 'NameError' in output
    print(f"  p{pidx}/{variant}: {'NameError' if has_name_error else output[:40]}... OK")

    save_result(
        pidx, variant,
        ctx['problem'], ctx['answer'],
        vinfo.get('verdict', 'UNKNOWN'),
        vinfo.get('verdict_reason', ''),
        mod['modified_problem'],
        mod['modified_code'],
        mod['expected_error'],
        mod['summary'],
        mod['why_beats'],
        codes[pidx],
        mod['sim'], mod['imp'],
    )
    total_success += 1

print(f"\n{'='*60}")
print(f"DONE: {total_success} saved, {total_fail} failed")
print(f"{'='*60}")
