import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Get all CSV files in cvpr folder except input.csv
cvpr_path = Path('cvpr')
csv_files = [f for f in cvpr_path.glob('*.csv') if f.name != 'input.csv']

print("="*120)
print("COMPREHENSIVE RATING STATISTICS TABLE - ALL CSV FILES")
print("="*120)

# Store rating statistics
rating_stats = []

for csv_file in sorted(csv_files):
    try:
        df = pd.read_csv(csv_file)

        # Extract file info
        file_name = csv_file.name
        file_type = 'train' if 'train' in file_name.lower() else ('test' if 'test' in file_name.lower() else 'valid')
        category = file_name.replace('.train.csv', '').replace('.test.csv', '').replace('.valid.csv', '').replace(' (1)', '')

        if 'rating' in df.columns:
            # Calculate rating distribution
            total_reviews = len(df)
            rating_dist = df['rating'].value_counts().sort_index()

            # Create stats dictionary
            stats = {
                'Category': category,
                'Type': file_type,
                'Total_Reviews': total_reviews,
                'Mean': round(df['rating'].mean(), 3),
                'Median': round(df['rating'].median(), 1),
                'Std_Dev': round(df['rating'].std(), 3),
                'Min': int(df['rating'].min()),
                'Max': int(df['rating'].max()),
            }

            # Add percentage for each rating (1-5)
            for rating in [1, 2, 3, 4, 5]:
                count = rating_dist.get(rating, 0)
                pct = (count / total_reviews) * 100
                stats[f'{int(rating)}_Star_%'] = round(pct, 2)
                stats[f'{int(rating)}_Star_Count'] = int(count)

            rating_stats.append(stats)

    except Exception as e:
        print(f"Error processing {csv_file.name}: {e}")

# Create DataFrame
df_stats = pd.DataFrame(rating_stats)

# Sort by Type then Category
df_stats = df_stats.sort_values(['Type', 'Category'])

print("\n" + "="*120)
print("PART 1: BASIC RATING STATISTICS")
print("="*120)
print("\n" + df_stats[['Category', 'Type', 'Total_Reviews', 'Mean', 'Median', 'Std_Dev', 'Min', 'Max']].to_string(index=False))

print("\n\n" + "="*120)
print("PART 2: RATING DISTRIBUTION (PERCENTAGES)")
print("="*120)
print("\n" + df_stats[['Category', 'Type', '1_Star_%', '2_Star_%', '3_Star_%', '4_Star_%', '5_Star_%']].to_string(index=False))

print("\n\n" + "="*120)
print("PART 3: RATING DISTRIBUTION (COUNTS)")
print("="*120)
print("\n" + df_stats[['Category', 'Type', '1_Star_Count', '2_Star_Count', '3_Star_Count', '4_Star_Count', '5_Star_Count']].to_string(index=False))

print("\n\n" + "="*120)
print("SUMMARY STATISTICS BY FILE TYPE")
print("="*120)

type_summary = df_stats.groupby('Type').agg({
    'Total_Reviews': 'sum',
    'Mean': 'mean',
    'Std_Dev': 'mean',
    '1_Star_%': 'mean',
    '2_Star_%': 'mean',
    '3_Star_%': 'mean',
    '4_Star_%': 'mean',
    '5_Star_%': 'mean'
}).round(2)

print("\n" + type_summary.to_string())

print("\n\n" + "="*120)
print("OVERALL STATISTICS (ALL FILES COMBINED)")
print("="*120)

print(f"\nTotal Reviews: {df_stats['Total_Reviews'].sum():,}")
print(f"Average Mean Rating: {df_stats['Mean'].mean():.3f}")
print(f"Average Std Dev: {df_stats['Std_Dev'].mean():.3f}")
print(f"\nAverage Rating Distribution:")
print(f"  1 Star: {df_stats['1_Star_%'].mean():.2f}%")
print(f"  2 Star: {df_stats['2_Star_%'].mean():.2f}%")
print(f"  3 Star: {df_stats['3_Star_%'].mean():.2f}%")
print(f"  4 Star: {df_stats['4_Star_%'].mean():.2f}%")
print(f"  5 Star: {df_stats['5_Star_%'].mean():.2f}%")

# Export to CSV
output_file = 'rating_statistics_summary.csv'
df_stats.to_csv(output_file, index=False)
print(f"\n✓ Full table exported to: {output_file}")

print("\n" + "="*120)
print("END OF REPORT")
print("="*120)
