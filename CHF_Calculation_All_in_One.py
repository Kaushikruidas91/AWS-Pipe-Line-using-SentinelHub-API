### Data Normalization ####
############################


import numpy as np
import pandas as pd

# Load the CSV file
df = pd.read_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable.csv")


# Define column groups for each normalization formula
columns_to_normalize_1 = ['NDVI_Max', 'LSWI_Max','Fapar', 'Rainfall_CHIRPS', 'VH_Max', 'VH_Sum']
columns_to_normalize_2 = ['CCV']

# Apply the first normalization formula
for col in columns_to_normalize_1:
    min_val = df[col].min()
    max_val = df[col].max()
    df[col + '_normalized'] = (df[col] - min_val) / (max_val - min_val)



# Apply the second normalization formula
for col in columns_to_normalize_2:
    min_val = df[col].min()
    max_val = df[col].max()
    df[col + '_normalized'] = (max_val - df[col]) / (max_val - min_val)

# Save the updated DataFrame with normalized columns to a new CSV file
df.to_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable_normalized.csv", index=False)


######### Entrophy Generation #########
#######################################
import numpy as np
import pandas as pd

# Load your CSV file
df = pd.read_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable_normalized.csv")

# Select the required columns
selected_columns = ['NDVI_Max_normalized', 'LSWI_Max_normalized',
                      'Rainfall_CHIRPS_normalized', 'VH_Sum_normalized', 'VH_Max_normalized',
                    'Fapar_normalized', 'CCV_normalized']

# Extract only the selected columns into a new DataFrame
data = df[selected_columns]

# Define a function to calculate the entropy for a single column
def calculate_entropy(column):
    # Ensure no zero or negative values by clipping the column (for log calculations)
    column = column.clip(lower=1e-12)
    
    # Calculate the probabilities by dividing each element by the column sum
    p_ij = column / column.sum()
    
    # Calculate entropy
    n = len(column)
    entropy = -(1 / np.log(n)) * np.sum(p_ij * np.log(p_ij))
    return entropy

# Apply the entropy calculation for each column and store results in a dictionary
entropy_results = {col: calculate_entropy(data[col]) for col in selected_columns}

# Convert the entropy results to a DataFrame
entropy_df = pd.DataFrame(list(entropy_results.items()), columns=['Feature', 'Entropy'])

# Save the entropy results to a new CSV file
entropy_df.to_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable_Entropy.csv", index=False)

print("Entropy calculation completed and saved to CSV.")


######## Weightage Generation #############
###########################################
import pandas as pd

# Load the entropy CSV file
entropy_df = pd.read_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable_Entropy.csv")

# Total number of features (m)
m = len(entropy_df)

# Calculate the sum of all entropy values
entropy_sum = entropy_df['Entropy'].sum()

# Define a function to calculate weight w_j for each feature
def calculate_weight(entropy, entropy_sum, m):
    weight = (1 - entropy) / (m - entropy_sum)
    return weight

# Apply the weight calculation to each row in the DataFrame
entropy_df['Weight'] = entropy_df['Entropy'].apply(lambda E_j: calculate_weight(E_j, entropy_sum, m))

# Save the weights to a new CSV file
entropy_df.to_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable_Weight.csv", index=False)

print("Weight calculation completed and saved to CSV.")


############ CHF Generation ############
########################################
import pandas as pd

# Load the weights and normalized data CSV files
weights_df = pd.read_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable_Weight.csv")  # Weightage CSV file
data_df = pd.read_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Variable_normalized.csv") # Normalized CSV file

# Select only the normalized feature columns and their weights
selected_columns = ['NDVI_Max_normalized', 'LSWI_Max_normalized',
                      'Rainfall_CHIRPS_normalized', 'VH_Sum_normalized', 'VH_Max_normalized',
                    'Fapar_normalized', 'CCV_normalized']

# Ensure the selected columns match the weight feature order
weights_df = weights_df[weights_df['Feature'].isin(selected_columns)].set_index('Feature')
weights = weights_df['Weight'].reindex(selected_columns).values  # Get weights in the correct order

# Calculate CHFi for each observation
data_df['CHF'] = data_df[selected_columns].dot(weights)

# Save the CHFi results to a new CSV file
data_df.to_csv(r"D:\CIPL_WORK\CHF_paddy\BAHRAICH_CHF_Work\Bahraich_All_CHF_Results_CHIRPS_data.csv", index=False)

print("CHF calculation completed and saved to CSV.")