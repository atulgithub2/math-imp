import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Get all CSV files in cvpr folder except input.csv
cvpr_path = Path('cvpr')
csv_files = [f for f in cvpr_path.glob('*.csv') if f.name != 'input.csv']

print("="*80)
print("EXPLORATORY DATA ANALYSIS REPORT - CVPR CSV FILES")
print("="*80)
print(f"\nTotal files analyzed: {len(csv_files)}")
print(f"Files: {[f.name for f in csv_files]}")
print("\n" + "="*80)

# Store summary statistics
all_stats = []

for csv_file in sorted(csv_files):
    print(f"\n{'='*80}")
    print(f"FILE: {csv_file.name}")
    print(f"{'='*80}")

    try:
        # Read CSV
        df = pd.read_csv(csv_file)

        # Basic info
        print(f"\n📊 BASIC INFORMATION")
        print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        # Data types
        print(f"\n📋 DATA TYPES")
        for col in df.columns:
            print(f"   {col}: {df[col].dtype}")

        # Missing values
        print(f"\n❓ MISSING VALUES")
        missing = df.isnull().sum()
        if missing.sum() == 0:
            print("   ✓ No missing values found")
        else:
            for col in missing[missing > 0].index:
                pct = (missing[col] / len(df)) * 100
                print(f"   {col}: {missing[col]:,} ({pct:.2f}%)")

        # Duplicates
        dup_count = df.duplicated().sum()
        print(f"\n🔄 DUPLICATES")
        print(f"   Total duplicate rows: {dup_count:,} ({(dup_count/len(df)*100):.2f}%)")

        # Unique values
        print(f"\n🔢 UNIQUE VALUES")
        for col in df.columns:
            n_unique = df[col].nunique()
            print(f"   {col}: {n_unique:,} unique values")

        # Rating analysis (if rating column exists)
        if 'rating' in df.columns:
            print(f"\n⭐ RATING ANALYSIS")
            print(f"   Mean rating: {df['rating'].mean():.2f}")
            print(f"   Median rating: {df['rating'].median():.2f}")
            print(f"   Std deviation: {df['rating'].std():.2f}")
            print(f"   Min rating: {df['rating'].min():.2f}")
            print(f"   Max rating: {df['rating'].max():.2f}")
            print(f"\n   Rating distribution:")
            rating_dist = df['rating'].value_counts().sort_index()
            for rating, count in rating_dist.items():
                pct = (count / len(df)) * 100
                bar = '█' * int(pct / 2)
                print(f"   {rating}: {count:,} ({pct:.1f}%) {bar}")

        # User analysis
        if 'user_id' in df.columns:
            print(f"\n👥 USER ANALYSIS")
            user_counts = df['user_id'].value_counts()
            print(f"   Total unique users: {df['user_id'].nunique():,}")
            print(f"   Avg reviews per user: {len(df) / df['user_id'].nunique():.2f}")
            print(f"   Max reviews by single user: {user_counts.max()}")
            print(f"   Min reviews by single user: {user_counts.min()}")
            print(f"   Users with only 1 review: {(user_counts == 1).sum():,}")

        # Product analysis
        if 'parent_asin' in df.columns:
            print(f"\n📦 PRODUCT ANALYSIS")
            product_counts = df['parent_asin'].value_counts()
            print(f"   Total unique products: {df['parent_asin'].nunique():,}")
            print(f"   Avg reviews per product: {len(df) / df['parent_asin'].nunique():.2f}")
            print(f"   Max reviews for single product: {product_counts.max()}")
            print(f"   Min reviews for single product: {product_counts.min()}")
            print(f"   Products with only 1 review: {(product_counts == 1).sum():,}")

            # Top 5 products
            print(f"\n   Top 5 most reviewed products:")
            for idx, (product, count) in enumerate(product_counts.head(5).items(), 1):
                print(f"   {idx}. {product}: {count:,} reviews")

        # Timestamp analysis
        if 'timestamp' in df.columns:
            print(f"\n📅 TIMESTAMP ANALYSIS")
            # Convert timestamp to datetime (handling both milliseconds and seconds)
            try:
                # Try milliseconds first
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
                # If all failed, try seconds
                if df['datetime'].isnull().all():
                    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')

                if not df['datetime'].isnull().all():
                    print(f"   Earliest review: {df['datetime'].min()}")
                    print(f"   Latest review: {df['datetime'].max()}")
                    print(f"   Time span: {(df['datetime'].max() - df['datetime'].min()).days} days")

                    # Year distribution
                    df['year'] = df['datetime'].dt.year
                    year_dist = df['year'].value_counts().sort_index()
                    print(f"\n   Reviews by year:")
                    for year, count in year_dist.items():
                        if pd.notna(year):
                            print(f"   {int(year)}: {count:,}")
                else:
                    print("   ⚠ Could not parse timestamps")
            except Exception as e:
                print(f"   ⚠ Error parsing timestamps: {e}")

        # Sample data
        print(f"\n📄 SAMPLE DATA (first 5 rows)")
        print(df.head().to_string(index=False))

        # Store summary stats
        file_type = 'train' if 'train' in csv_file.name else ('test' if 'test' in csv_file.name else 'valid')
        category = csv_file.name.replace('.train.csv', '').replace('.test.csv', '').replace('.valid.csv', '').replace(' (1)', '')

        all_stats.append({
            'File': csv_file.name,
            'Category': category,
            'Type': file_type,
            'Rows': df.shape[0],
            'Users': df['user_id'].nunique() if 'user_id' in df.columns else 0,
            'Products': df['parent_asin'].nunique() if 'parent_asin' in df.columns else 0,
            'Avg_Rating': df['rating'].mean() if 'rating' in df.columns else 0,
            'Rating_Std': df['rating'].std() if 'rating' in df.columns else 0,
        })

    except Exception as e:
        print(f"\n❌ Error processing file: {e}")

# Summary table
print(f"\n\n{'='*80}")
print("SUMMARY TABLE - ALL FILES")
print(f"{'='*80}\n")

summary_df = pd.DataFrame(all_stats)
if not summary_df.empty:
    summary_df = summary_df.sort_values('Rows', ascending=False)
    print(summary_df.to_string(index=False))

    print(f"\n{'='*80}")
    print("AGGREGATE STATISTICS")
    print(f"{'='*80}")
    print(f"Total rows across all files: {summary_df['Rows'].sum():,}")
    print(f"Total unique users: {summary_df['Users'].sum():,}")
    print(f"Total unique products: {summary_df['Products'].sum():,}")
    print(f"Average rating across all files: {summary_df['Avg_Rating'].mean():.2f}")
    print(f"File type distribution:")
    print(summary_df['Type'].value_counts().to_string())

    print(f"\n{'='*80}")
    print("TOP 5 LARGEST FILES")
    print(f"{'='*80}")
    for idx, row in summary_df.head(5).iterrows():
        print(f"{row['File']}: {row['Rows']:,} rows")

    print(f"\n{'='*80}")
    print("RATING STATISTICS BY FILE TYPE")
    print(f"{'='*80}")
    type_stats = summary_df.groupby('Type').agg({
        'Rows': 'sum',
        'Avg_Rating': 'mean',
        'Rating_Std': 'mean'
    })
    print(type_stats.to_string())

print(f"\n{'='*80}")
print("END OF REPORT")
print(f"{'='*80}")
