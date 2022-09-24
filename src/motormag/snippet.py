import motormag
import pandas as pd
from matplotlib import pyplot as plt

df = pd.read_pickle(r'C:\Users\brava\OneDrive\src\science\motormag\maglev.df')
f, axes = plt.subplots(2, 3)
axes = axes.flatten()
for i in range(6):
    motormag.draw.plot_strength_2d(df, 'y', i, field_axis='x', vmin=df.mag_x.min(), vmax=df.mag_x.max(), ax=axes[i])
f.tight_layout()
plt.show()