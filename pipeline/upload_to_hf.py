#!/usr/bin/env python3
"""
Upload results to HuggingFace dataset: thulthula/math-examples

Usage:
    python3 upload_to_hf.py                    # Upload all successful results
    python3 upload_to_hf.py --all              # Upload all results (including failures)
    python3 upload_to_hf.py --dry-run          # Preview data without uploading
    python3 upload_to_hf.py --yes              # Skip confirmation prompt
"""

import json
import os
import argparse
from pathlib import Path
from datasets import Dataset
from huggingface_hub import HfApi

def load_full_results(results_dir="results", require_variation=True):
    """Load all full result files with DAG information.

    Args:
        require_variation: If True, only include problems with at least one successful variation
    """
    results = []
    results_path = Path(results_dir)

    if not results_path.exists():
        print(f"Error: {results_dir} directory not found!")
        return []

    json_files = sorted(results_path.glob("problem_*.json"))
    print(f"Found {len(json_files)} result files")

    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Check if at least one variation succeeded
        if require_variation:
            variations = data.get('variations', {})
            node_success = variations.get('variation_1_node_deletion', {}).get('success', False)
            edge_success = variations.get('variation_2_edge_deletion', {}).get('success', False)

            # Skip if no variations succeeded
            if not (node_success or edge_success):
                continue

        results.append(data)

    return results

def prepare_dataset(results):
    """Convert results to HuggingFace dataset format with DAGs."""
    if not results:
        print("No results to upload!")
        return None

    # Prepare data in columnar format
    dataset_dict = {
        "id": [],
        "original_question": [],
        "original_answer": [],
        "node_deletion_question": [],
        "node_deletion_dag": [],
        "edge_deletion_question": [],
        "edge_deletion_dag": [],
        "success": []
    }

    for result in results:
        dataset_dict["id"].append(result.get("index", -1))
        dataset_dict["original_question"].append(result.get("original_question", ""))
        dataset_dict["original_answer"].append(result.get("original_answer", ""))

        # Extract node deletion variation
        variations = result.get("variations", {})
        node_var = variations.get("variation_1_node_deletion", {})
        if node_var.get("success"):
            node_result = node_var.get("result", {})
            dataset_dict["node_deletion_question"].append(node_result.get("modified_problem", ""))
            # Convert DAG to JSON string for storage
            dag = node_result.get("modified_dag", None)
            dataset_dict["node_deletion_dag"].append(json.dumps(dag) if dag else "")
        else:
            dataset_dict["node_deletion_question"].append("")
            dataset_dict["node_deletion_dag"].append("")

        # Extract edge deletion variation
        edge_var = variations.get("variation_2_edge_deletion", {})
        if edge_var.get("success"):
            edge_result = edge_var.get("result", {})
            dataset_dict["edge_deletion_question"].append(edge_result.get("modified_problem", ""))
            # Convert DAG to JSON string for storage
            dag = edge_result.get("modified_dag", None)
            dataset_dict["edge_deletion_dag"].append(json.dumps(dag) if dag else "")
        else:
            dataset_dict["edge_deletion_question"].append("")
            dataset_dict["edge_deletion_dag"].append("")

        dataset_dict["success"].append(result.get("success", False))

    return Dataset.from_dict(dataset_dict)

def upload_to_huggingface(dataset, repo_id="thulthula/math-examples", split="train", token=None):
    """Upload dataset to HuggingFace Hub."""
    print(f"\nUploading to {repo_id}...")
    print(f"Dataset size: {len(dataset)} examples")
    print(f"Split: {split}")

    try:
        # Push to hub
        dataset.push_to_hub(
            repo_id=repo_id,
            split=split,
            token=token,
            private=False  # Set to True if you want a private dataset
        )
        print(f"\n✓ Successfully uploaded to https://huggingface.co/datasets/{repo_id}")
        return True
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        print("\nMake sure you:")
        print("1. Have huggingface_hub installed: pip install huggingface_hub")
        print("2. Provide a valid HF token via --token or HF_TOKEN environment variable")
        print("3. Have write access to the repository")
        print("\nGet your token at: https://huggingface.co/settings/tokens")
        return False

def main():
    parser = argparse.ArgumentParser(description="Upload results to HuggingFace")
    parser.add_argument("--all", action="store_true",
                        help="Upload all results including those with no variations (default: only with variations)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview data without uploading")
    parser.add_argument("--repo-id", type=str, default="thulthula/math-examples",
                        help="HuggingFace repo ID (default: thulthula/math-examples)")
    parser.add_argument("--split", type=str, default="train",
                        help="Dataset split name (default: train)")
    parser.add_argument("--results-dir", type=str, default="results",
                        help="Directory with full results (default: results)")
    parser.add_argument("--token", type=str, default=None,
                        help="HuggingFace API token (or use HF_TOKEN env var)")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt and proceed with upload")
    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.getenv('HF_TOKEN')
    if not token and not args.dry_run:
        print("\n⚠ Warning: No HuggingFace token provided!")
        print("Upload will fail unless you're already logged in.")
        print("\nOptions:")
        print("1. Pass token: --token YOUR_TOKEN")
        print("2. Set environment: export HF_TOKEN=YOUR_TOKEN")
        print("3. Get token at: https://huggingface.co/settings/tokens")
        print()

    print("=" * 70)
    print("  Upload to HuggingFace Dataset")
    print("=" * 70)
    print()

    # Load results
    require_variation = not args.all
    print(f"Loading results (require_at_least_one_variation={require_variation})...")
    results = load_full_results(args.results_dir, require_variation)

    if not results:
        print("No results found!")
        return

    print(f"Loaded {len(results)} results")

    # Count variations
    both_vars = 0
    node_only = 0
    edge_only = 0
    for r in results:
        variations = r.get('variations', {})
        node_success = variations.get('variation_1_node_deletion', {}).get('success', False)
        edge_success = variations.get('variation_2_edge_deletion', {}).get('success', False)

        if node_success and edge_success:
            both_vars += 1
        elif node_success:
            node_only += 1
        elif edge_success:
            edge_only += 1

    print(f"  - Both variations: {both_vars}")
    print(f"  - Node deletion only: {node_only}")
    print(f"  - Edge deletion only: {edge_only}")
    print(f"  - Total with at least one variation: {both_vars + node_only + edge_only}")
    print()

    # Prepare dataset
    print("Preparing dataset...")
    dataset = prepare_dataset(results)

    if dataset is None:
        return

    print(f"Dataset created with {len(dataset)} examples")
    print(f"Features: {list(dataset.features.keys())}")
    print()

    # Show sample
    print("Sample (first example):")
    print("-" * 70)
    sample = dataset[0]
    print(f"ID: {sample['id']}")
    print(f"Original Question: {sample['original_question'][:100]}...")
    print(f"Original Answer: {sample['original_answer']}")
    print(f"Node Deletion Question: {sample['node_deletion_question'][:100] if sample['node_deletion_question'] else 'None'}...")
    print(f"Node Deletion DAG: {'Present' if sample['node_deletion_dag'] else 'None'}")
    print(f"Edge Deletion Question: {sample['edge_deletion_question'][:100] if sample['edge_deletion_question'] else 'None'}...")
    print(f"Edge Deletion DAG: {'Present' if sample['edge_deletion_dag'] else 'None'}")
    print(f"Success: {sample['success']}")
    print("-" * 70)
    print()

    # Upload or dry run
    if args.dry_run:
        print("DRY RUN - Not uploading")
        print(f"Would upload {len(dataset)} examples to {args.repo_id}")
    else:
        # Confirm upload
        print(f"Ready to upload {len(dataset)} examples to {args.repo_id}")

        if args.yes:
            response = 'yes'
        else:
            response = input("Continue? (yes/no): ").strip().lower()

        if response == 'yes':
            success = upload_to_huggingface(dataset, args.repo_id, args.split, token)
            if success:
                print("\n✓ Upload complete!")
        else:
            print("Upload cancelled")

if __name__ == "__main__":
    main()
