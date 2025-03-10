import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load CSV file (Ensure 'data.csv' exists in the same directory)
file_path = "data.csv"
df = pd.read_csv(file_path)

# Display basic information
print("Dataset Overview:")
print(df.info())

# Display first few rows
print("\nFirst 5 Rows:")
print(df.head())

# Summary statistics
print("\nSummary Statistics:")
print(df.describe())

# Check for missing values
print("\nMissing Values:")
print(df.isnull().sum())

# ❌ Blunder: Trying to plot a non-existent column "non_existent_column"
plt.figure(figsize=(8, 5))
sns.histplot(df["non_existent_column"], kde=True, bins=30)  # This column doesn't exist in the dataset!
plt.title("Distribution of non_existent_column")
plt.xlabel("non_existent_column")
plt.ylabel("Frequency")
plt.show()

# ❌ Blunder: Trying to make a scatter plot with non-existent columns
plt.figure(figsize=(8, 5))
sns.scatterplot(x=df["non_existent_column_x"], y=df["non_existent_column_y"])  # These columns don't exist either!
plt.title("Scatter Plot of non_existent_column_x vs non_existent_column_y")
plt.xlabel("non_existent_column_x")
plt.ylabel("non_existent_column_y")
plt.show()
