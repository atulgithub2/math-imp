# Weak Impossible Variants — AIME 2026

74 total hits across 12 (problem, variant) pairs. Below is each problem with the original, the impossible variant, and why the deletion was too weak.

---

## Problem 18 — **41 hits** (edge: 21, node: 20) — 6 models

**Original:**
> For each positive integer $n$ let $f(n)$ be the value of the base-ten numeral $n$ viewed in base $b$, where $b$ is the least integer greater than the greatest digit in $n$. For example, if $n=72$, then $b=8$, and $72$ as a numeral in base $8$ equals $7\cdot 8+2=58$; therefore $f(72)=58$. Find the number of positive integers $n$ less than $1000$ such that $f(n)=n$.

**Impossible (edge):**
> For each positive integer $n$, let $f(n)$ be the value of the base-ten numeral $n$ viewed in some base $b$, where $b$ is determined by the digits of $n$ according to some rule. Find the number of positive integers $n$ less than $1000$ such that $f(n)=n$.

**Impossible (node):**
> For each positive integer $n$ let $f(n)$ be the value of the base-ten numeral $n$ viewed in some base $b$ determined by the digits of $n$. Find the number of positive integers $n$ less than $1000$ such that $f(n)=n$.

**Why it's weak:** This is a well-known AIME problem. The "deletion" replaced the specific rule ("least integer greater than the greatest digit") with "some rule" / "determined by the digits", but models recognize the original problem from the remaining structure ($f(n)=n$, base-ten numeral viewed in base $b$, $n<1000$). The problem is essentially unique — there's only one natural rule that makes $f(n)=n$ interesting, so models reconstruct it.

---

## Problem 21 — **11 hits** (edge: 7, node: 4) — 3 models

**Original:**
> A standard fair six-sided die is rolled repeatedly. Each time the die reads 1 or 2, Alice gets a coin; each time it reads 3 or 4, Bob gets a coin; and each time it reads 5 or 6, Carol gets a coin. The probability that Alice and Bob each receive at least two coins before Carol receives any coins can be written as $\tfrac mn$, where $m$ and $n$ are relatively prime positive integers. Find $100m+n$.

**Impossible (edge):**
> ...Each time the die reads 1 or 2, Alice gets a coin; **some unspecified faces give Bob a coin**; and the remaining faces give Carol a coin...

**Impossible (node):**
> ...each time it reads 3 or 4, Bob gets a coin; and each time it reads 5 or 6, Carol gets a coin. The probability that Alice and Bob each receive at least **some number of** coins before Carol receives any coins...

**Why it's weak:**
- **Edge deletion:** With 6 faces and Alice getting {1,2}, the only symmetric assignment is Bob={3,4}, Carol={5,6}. There's essentially one natural partition, so "some unspecified faces" is trivially recoverable.
- **Node deletion:** Replaced "two" with "some number of". The rest of the problem is fully specified, and models recognize the original AIME problem and fill in "two".

---

## Problem 7 — **10 hits** (node: 10) — 6 models

**Original:**
> Let $N$ be the number of positive integer divisors of $17017^{17}$ that leave a remainder of $5$ upon division by $12$. Find the remainder when $N$ is divided by $1000$.

**Impossible (node):**
> Let $N$ be the number of positive integer divisors of **some number raised to the 17th power** that leave a remainder of $5$ upon division by $12$. **The base number has four distinct prime factors.** Find the remainder when $N$ is divided by $1000$.

**Why it's weak:** The deletion removed "17017" but added the hint "four distinct prime factors." Since $17017 = 7 \times 11 \times 13 \times 17$ is a very well-known AIME factorization, and the problem keeps the exponent 17, the remainder 5 mod 12, and the hint about four prime factors, models easily recognize and reconstruct the original number.

---

## Problem 25 — **7 hits** (edge: 6, node: 1) — 3 models

**Original:**
> Find the greatest integer $n$ such that the cubic polynomial $x^{3} -\frac{n}{6}x^{2} + (n - 11)x - 400$ has roots $\alpha^{2}$, $\beta^{2}$, and $\gamma^{2}$... exactly seven different possible values for $\alpha + \beta + \gamma$.

**Impossible (edge):**
> ...$(n - 11)x - 400$... exactly **$k$ different possible values** for $\alpha + \beta + \gamma$, **where $k$ is some unspecified number**.

**Impossible (node):**
> ...$x^{3} -\frac{n}{6}x^{2} + (n - c)x - 400$... exactly seven different possible values... **$c$ is some constant whose value is not given.**

**Why it's weak:**
- **Edge deletion:** The polynomial coefficients $\frac{n}{6}$, $(n-11)$, and $-400$ are all kept. The constraint "exactly $k$ values" is replaced with "some unspecified $k$", but the answer ("greatest integer $n$") depends mainly on the polynomial structure. Models solve for $n$ using the polynomial constraints alone and get the same answer.
- **Node deletion:** Replacing 11 with unknown $c$ while keeping "seven different possible values" doesn't help — models recognize the original and substitute $c=11$.

---

## Problem 15 — **1 hit** (edge: 1) — 1 model (sonnet-4.6)

**Original:**
> Find the sum of the 11th terms of all arithmetic sequences of integers that have first term equal to 4 and include both 24 and 34 as terms.

**Impossible (edge):**
> ...have first term equal to 4 and include both **some value p and some value q** as terms.

**Why it's weak:** Only 1 hit — likely a lucky guess or the model recognized the problem from "first term 4, 11th terms, arithmetic sequences of integers." Low concern.

---

## Problem 16 — **1 hit** (edge: 1) — 1 model (mistral-lg3)

**Original:**
> The figure below shows a grid of 10 squares in a row. Each square has a diagonal connecting its lower left vertex to its upper right vertex...

**Impossible (edge):**
> ...Each square **may contain some additional segments connecting vertices**...

**Why it's weak:** 1 hit only — likely the model recognized the classic grid path-counting problem from the remaining structure (10 squares, A to B, no right-to-left). Low concern.

---

## Problem 23 — **1 hit** (edge: 1) — 1 model (kimi-k2.5)

**Original:**
> Let $S = \frac{1}{9}+\frac{1}{99}+\frac{1}{999}+\cdots$. Find the remainder when $\lfloor 10^{100}S \rfloor$ is divided by $1000$.

**Impossible (edge):**
> ...Find the remainder when $\lfloor 10^{N}S \rfloor$ is divided by $M$.

**Why it's weak:** 1 hit — model likely recognized the series and guessed $N=100$, $M=1000$. Low concern.

---

## Problem 19 — **1 hit** (node: 1) — 1 model (mistral-lg3)

**Original:**
> ...the probability that exactly 4 of them are red equals the probability that exactly 5 of them are red...

**Impossible (node):**
> ...the probability that exactly 4 of them are red equals the probability that exactly **some unknown number** of them are red...

**Why it's weak:** 1 hit only. Replacing "5" with "some unknown number" is technically impossible, but the most natural guess is 5 (next integer after 4). Low concern.

---

## Problem 1 — **1 hit** (node: 1) — 1 model (deepseek-v3.2)

**Original:**
> ...palindromes... whose digits add up to 13.

**Impossible (node):**
> ...palindromes... whose digits add up to **some target value**.

**Why it's weak:** 1 hit only — likely coincidence. Low concern.

---

## Summary

| Severity | Problems | Total Hits | Issue |
|----------|----------|------------|-------|
| **Critical** | 18 | 41 | "Some rule" deletion preserves too much structure; problem is uniquely recognizable |
| **High** | 7, 21 | 21 | Deleted value is trivially recoverable from context (factorization hint, symmetric partition) |
| **Medium** | 25 | 7 | Polynomial structure constrains answer regardless of deleted value |
| **Low** | 1, 15, 16, 19, 23 | 5 | 1 hit each — likely coincidence or lucky guesses |
