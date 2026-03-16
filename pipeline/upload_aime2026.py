import re
from datasets import Dataset

# Read the file
with open("AIME2026.txt", "r") as f:
    content = f.read()

# Split on the pattern: `}}` at end of a block followed by `{{` starting a new block
blocks = re.split(r'\}\}\s*,?\s*\n\s*\n\s*\{\{', content)

# Clean first block: remove leading `{` or `{{`
blocks[0] = re.sub(r'^\s*\{\s*\n?\s*\{?', '', blocks[0])
# Clean last block: remove trailing `}}` and whitespace
blocks[-1] = re.sub(r'\}\}\s*$', '', blocks[-1])

records = []

for i, block in enumerate(blocks):
    block = block.strip()
    if not block:
        continue

    # Find the boundary between problem and solution
    sol_match = re.search(r'\},?\s*\n+\s*\{', block)

    if not sol_match:
        print(f"WARNING: Could not find solution boundary in block {i+1}: {block[:100]}")
        continue

    problem_part = block[:sol_match.start()].strip()
    solution_part = block[sol_match.end():].strip()  # after the `{`

    # Clean problem text - remove "Problem [N]" header
    problem_text = re.sub(r'^\s*Problem\s*\d*\s*\n?', '', problem_part).strip()
    problem_text = problem_text.rstrip('}').strip()

    # Clean solution - remove "Solution N (description)" header
    solution_text = re.sub(r'^Solution\s*\d*\s*(\([^)]*\))?\s*\n?', '', solution_part).strip()
    if solution_text.startswith('{'):
        solution_text = solution_text[1:].strip()

    # Extract final answer from \boxed{} - handle nested braces like \boxed{\textbf{244}}
    boxed_matches = re.findall(r'\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', solution_text)
    if boxed_matches:
        final_answer = boxed_matches[-1].strip()
        # Clean up LaTeX formatting: \textbf{X} -> X
        final_answer = re.sub(r'\\textbf\{([^}]*)\}', r'\1', final_answer)
        # Remove any remaining LaTeX commands
        final_answer = final_answer.strip()
    else:
        final_answer = ""
        print(f"WARNING: No \\boxed answer found in problem {i+1}")
        print(f"  Solution tail: ...{solution_text[-100:]}")

    records.append({
        "number": i + 1,
        "problem": problem_text,
        "final_answer": final_answer,
        "solution": solution_text,
    })

# No manual fixes needed

print(f"Extracted {len(records)} problems:\n")
for r in records:
    ans = r['final_answer'] if r['final_answer'] else "MISSING"
    print(f"  Problem {r['number']:2d}: answer = {ans}")

# Create and push dataset
ds = Dataset.from_list(records)
print(f"\nDataset: {ds}")
ds.push_to_hub("thulthula/AIME2026")
print("\nDataset pushed to thulthula/AIME2026")
