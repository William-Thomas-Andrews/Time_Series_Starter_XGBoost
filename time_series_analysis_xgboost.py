# -*- coding: utf-8 -*-
"""Time_Series_Analysis_XGBoost.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nNftJiG1pHOEbFFTVm-q4AVKy-6sjACU
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from matplotlib import pyplot as plt

df = pd.read_csv('sample_data/Month_Value_1.csv')

df

df.info()

df.describe()

df['Revenue'].plot(kind='hist', bins=20, title='Revenue')
plt.gca().spines[['top', 'right',]].set_visible(False)

df.shape

df['Period'] = pd.to_datetime(df['Period'])

df.isnull().sum()

from sklearn.impute import KNNImputer
knn = KNNImputer(n_neighbors=5, add_indicator=True)
df_transformed = pd.DataFrame(knn.fit_transform(df.drop(columns = ['Period'])))

df_transformed

df.isnull().sum()

df['Revenue'] = df_transformed[0]
df['Sales_quantity'] = df_transformed[1]
df['Average_cost'] = df_transformed[2]
df['The_average_annual_payroll_of_the_region'] = df_transformed[3]

df

df.isnull().sum()

df.columns[1:len(df.columns)]

df.dtypes

"""## Let's get rid of the outliers (in this case we will turn them into NAs)"""

def remove_outliers(df):



    def remove_outliers_columns(column):

      med = np.median(column)
      q75, q25 = np.percentile(column, [75 ,25])
      iqr = q75 - q25
      upper_bound = (1.5 * iqr) + q75
      lower_bound = (1.5 * iqr) - q25

      # Initialize a list to store new column values
      new_column = []

        # Iterate through values in the column
      for value in column:
            # Check if the value is an outlier
          if (value < lower_bound) or (value > upper_bound):
                # If it's an outlier, append np.nan
              new_column.append(np.nan)
          else:
                # If it's not an outlier, append the original value
              new_column.append(value)

      return(new_column)


    for i in df.columns[1:len(df.columns)]:
      df[i] = remove_outliers_columns(df[i])

    return(df)

remove_outliers(df)

df.isnull().sum()

"""## Now let's go back and impute those outliers"""

from sklearn.impute import KNNImputer
knn = KNNImputer(n_neighbors=5, add_indicator=True)
df_transformed = pd.DataFrame(knn.fit_transform(df.drop(columns = ['Period'])))

df['Revenue'] = df_transformed[0]
df['Sales_quantity'] = df_transformed[1]
df['Average_cost'] = df_transformed[2]
df['The_average_annual_payroll_of_the_region'] = df_transformed[3]

df.isnull().sum()



df.corr()

"""## We can see a high positive correlation between Sales_quantity and Revenue. This makes sense; the more you sell, the more revenue you earn.

## Now let's get our data ready for XGBOOST
"""

df = df.set_index('Period')
df.index = pd.to_datetime(df.index)

train = df.loc[df.index < pd.to_datetime('01-01-2021')]
test = df.loc[df.index >= pd.to_datetime('01-01-2021')]

train.count()

test.count()

from sklearn.preprocessing import StandardScaler as SS
ss = SS()

X_train = ss.fit_transform(train.drop(columns = 'Revenue'))
y_train = train['Revenue']
X_test = ss.transform(test.drop(columns = 'Revenue'))
y_test = test['Revenue']

"""## Initializing and performing the XGBOOST"""

import xgboost as XGB
reg = XGB.XGBRegressor(n_estimators = 1000, early_stopping_rounds = 50)
reg.fit(X_train, y_train, eval_set = [(X_train, y_train), (X_test, y_test)], verbose=True)

reg.feature_importances_

"""## As expected, the sales quantity has the highest importance in this model that predicts revenue.

## Let's plot these predictions
"""

test['prediction'] = reg.predict(X_test)
df = df.merge(test[['prediction']], how='left', left_index=True, right_index=True)
ax = df[['Revenue']].plot(figsize=(15, 5), style='o')
df['prediction'].plot(ax=ax, style='o', markersize=2)
plt.legend(['Truth Data', 'Predictions'])
ax.set_title('Raw Data and Prediction')
plt.show()

"""## The predictions are right on target, but because we used KNN imputer for much of the data, our results are a bit weird as you can see."""

prediction = pd.DataFrame(reg.predict(X_train), columns=['prediction'])
prediction.head()

missing_values_indices = df[df['prediction'].isna()].index

# Replace missing values with values from prediction
df.loc[missing_values_indices, 'prediction'] = prediction.iloc[:len(missing_values_indices), 0].values

df.head()

ax = df[['Revenue']].plot(figsize=(15, 5), style='o')
df['prediction'].plot(ax=ax, style='o', markersize=2)
plt.legend(['Truth Data', 'Predictions'])
ax.set_title('Raw Data and Prediction')
plt.show()

"""## The model does a great job, but keep in mind this data originally had so much missing data and many outliers that were all imputed, so it is hard to tell if this is a job well done.

## Let's determine the Root Mean Squared Error to evaluate how close the model's predictions were, by creating a simple function.
"""

def do_RMSE(true, prediction):

  import numpy as np

  n = len(prediction)
  y = true
  yhat = prediction

  MSE = (np.sum((y - yhat) ** 2)) / n
  RMSE = np.sqrt(MSE)

  return(RMSE)

y_pred1 = reg.predict(X_train)
do_RMSE(y_train, y_pred1)

y_pred2 = reg.predict(X_test)
do_RMSE(y_test, y_pred2)

"""## The model's predictions are off by about \$419 on average for the training data, and for the testing data, the model's predictions are off by about \$0.26 on average. However, this model may have its flaws as not only were many missing values imputed, but many outliers were also imputed. This is the reason why the model is so easily able to predict the values for the data."""