import pandas as pd
import numpy as np

# Load CSV
df = pd.read_csv("tracking_results.csv")

df['X_center'] = (df['X Min'] + df['X Max']) / 2
df['Y_center'] = (df['Y Min'] + df['Y Max']) / 2

df['dx'] = df['X_center'].diff()
df['dy'] = df['Y_center'].diff()
df['distance'] = np.sqrt(df['dx']**2 + df['dy']**2)

frame_rate = 30
time_per_frame = 1 / frame_rate

df['speed (pixels/sec)'] = df['distance'] / time_per_frame

df['speed (pixels/sec)'] = df['speed (pixels/sec)'].fillna(0)

print(df[['Frame Index', 'X_center', 'Y_center', 'speed (pixels/sec)']])
