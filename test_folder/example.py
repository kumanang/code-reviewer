import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pylab import rcParams

df = pd.read_csv('/content/gdrive/My Drive/Datasets/Emission.csv',parse_dates=['Year-Month'],index_col=0)
print(df.info()) print(df.head())

df.plot(figsize=(20,7))
plt.grid()

# find seasonality
from statsmodels.tsa.seasonal import seasonal_decompose
from pylab import rcParams
rcParams['figure.figsize'] = 18,7
decompose = seasonal_decompose(df)
decompose.plot()

train = df[0:int(len(df)*0.8)]
test = df[int(len(df)*0.8):]

train['CO2 Emission'].plot(fontsize=14)
test['CO2 Emission'].plot(fontsize=14)
plt.legend(['Training Data','Test Data'])
plt.show()

from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
ses_train = train.copy()
ses_test = test.copy()

model_ses = SimpleExpSmoothing(ses_train['CO2 Emission'])
model_ses_autofit = model_ses.fit(optimized=True)
model_ses_autofit.params
ses_test['predict']= model_ses_autofit.forecast(len(ses_test))

plt.figure(figsize=(16,8))
plt.plot(ses_train['CO2 Emission'], label='Train')
plt.plot(ses_test['CO2 Emission'], label='Test')

plt.plot(ses_test['predict'], label='Alpha =0.995 Simple Exponential Smoothing predictions on Test Set')

plt.legend(loc='best')
plt.grid()
plt.title('Alpha =0.995 Predictions');

from sklearn import metrics
rmse_model5_test_1 = metrics.mean_squared_error(ses_test['CO2 Emission'],ses_test['predict'],squared=False)
print(rmse_model5_test_1)

des_train = train.copy()
des_test = test.copy()

model_des = Holt(des_train['CO2 Emission'])
model_des_alpha = model_des.fit(optimized=True)

des_train['predict'] = model_des_alpha.fittedvalues
des_test['predict'] = model_des_alpha.forecast

rmse_des_train = metrics.mean_squared_error(des_train['CO2 Emission'],des_train['predict'],squared=False)
#rmse_des_test = metrics.mean_squared_error(des_test['CO2 Emission'],des_test['predict'],squared=False)
#print(rmse_des_test)
print(rmse_des_train)

lgses_train = np.log(train.copy())
lgses_test = np.log(test.copy())
lg_model_ses = SimpleExpSmoothing(lgses_train['CO2 Emission'])
lgmodel_ses_autofit = lg_model_ses.fit(optimized=True)

lgmodel_ses_autofit.params
lgses_test['predict']= lgmodel_ses_autofit.forecast(len(lgses_test))

plt.figure(figsize=(16,8))
plt.plot(lgses_train['CO2 Emission'], label='Train')
plt.plot(lgses_test['CO2 Emission'], label='Test')

plt.plot(lgses_test['predict'], label='Alpha =0.995 Simple Exponential Smoothing predictions on Test Set')

plt.legend(loc='best')
plt.grid()
plt.title('Alpha =0.995 Predictions');

from sklearn import metrics
rmse_model5_test_lg = metrics.mean_squared_error(lgses_test['CO2 Emission'],lgses_test['predict'],squared=False)
print(rmse_model5_test_lg)

def plot_results(train, test, prediction, title):
    plt.figure(figsize=(16,8))
    plt.plot(train['CO2 Emission'], label='Train')
    plt.plot(test['CO2 Emission'], label='Test')
    plt.plot(prediction, label=title)
    plt.legend(loc='best')
    plt.grid()
    plt.title(title)

plot_results(ses_train, ses_test, ses_test['predict'], 'Alpha =0.995 Predictions')
