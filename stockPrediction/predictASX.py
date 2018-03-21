
# TODO: Since x_train is rolling_window timesteps behind y_train, 
#       we are predicting the next day's close based on the last 2 months. 
#       Try predicting further into the future.
# TODO: rewrite so that additional features can be added such as NLP results.
# TODO: Incorporate grid search for hyperparameter choosing

# FIXME: change back to 60 days rolling window?

##############################################################################
# PART 1: Preparing the data
##############################################################################

import numpy as np
import pandas as pd
import glob
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

## Global Variables
stock = 'KRC'
rolling_window = 5
path = '/Users/admin/Documents/ASXdata/'


def dataImport(root_path, folder_string):
    csv_files = glob.glob(path + folder_string, recursive=True)
    csv_files.sort()
    temp_cv = pd.read_csv(csv_files[0], header=0, index_col=0,
                          names=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'],
                          parse_dates=['Date'])
    rawdata = []
    for i in range(0, len(csv_files)):
        temp_cv = pd.read_csv(csv_files[i], header=0, index_col=0,
                              names=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'],
                              parse_dates=['Date'])
        try:
            rawdata.append(temp_cv.ix[stock])
        except KeyError:
            print(stock + " not found at " + str(temp_cv.ix[0, 'Date']))
    processed_data = pd.DataFrame(rawdata)
    processed_data = processed_data.reset_index(drop=True)
    processed_data = processed_data.iloc[:, 1:]  
    # currently in format [Open, High, Low, Close, Volume].
    # We reorganize:
    cols = ['Open', 'High', 'Low', 'Volume','Close']
    processed_data = processed_data[cols]
    print('End of data import.')
    return processed_data

# importing the data
training_set = dataImport(path, folder_string= '201*/*')

# Pre-processing and feature scaling
print('Beginning Pre-processing.')
sc = MinMaxScaler(feature_range=(0,1))
training_set_scaled = sc.fit_transform(training_set)  
# [Open, High, Low, Close, Volume]

# Creating a data structure with rolling_window time steps and 1 output.
# The RNN will learn from rolling_window time steps.
x_train = []
y_train = []
for i in range(rolling_window, training_set.shape[0]-5):  # starting at rolling_window and going to the end of the training data
    x_train.append(training_set_scaled[i - rolling_window:i, :4])  # creates a sliding window of memory of size rolling_window
    y_train.append(training_set_scaled[i, 4])  # training set only contains one dimension now

x_train, y_train = np.array(x_train, dtype='float'), np.array(y_train, dtype='float')

# Reshaping data structure for training for use with TensorFlow.
x_train = np.reshape(x_train,
                     (x_train.shape[0], x_train.shape[1], 4),
                     1)
y_train = np.reshape(y_train,
                     (y_train.shape[0], 1))
print('x_train, y_train have been created, beginning creation of Neural Network.')
##############################################################################
# PART 2: Building the LSTM network
##############################################################################

# Importing relevant libraries
from keras.models import Sequential, load_model
from keras.layers import Dense, LSTM, Dropout

# Initialize the RNN
print("Initializing Neural Network.")
print("Learning from 4 features.")

hidden_layers = 2
layer_units = [25, 25, 25, 25]
units_l1 = 25
units_l2 = 25
units_l3 = 25
units_l4 = 25
dropout_rate = 0.2
optim = 'adam' # Another popular optmizer usually good for RNNs is RMSprop
input_shape = (x_train.shape[1], 4)
    
regressor = Sequential()  # predicting a continuous output/value, so its a regression.
# Adding the LSTM layers and some dropout regularization to avoid overfitting
# Remember, dropout turns off some neurons
# 50 units for high dimensionality problems like financial analysis
regressor.add(LSTM(units = layer_units[0], # FIRST LAYER
                   return_sequences = True,
                   input_shape = input_shape))
regressor.add(Dropout(rate=dropout_rate,))
print("First Layer created.")
regressor.add(LSTM(units = layer_units[0], # SECOND LAYER
                   return_sequences = False))
regressor.add(Dropout(rate=dropout_rate,))
print("Second layer created - Hidden Layer.")
regressor.add(Dense(units=1))
print('Output Layer created.')
print('Compiling Neural Network model.')

# Compiling the RNN
regressor.compile(optimizer=optim,
                  loss= 'mean_squared_error')
print("Compilation successful. Initializing training sequence.")
# Fitting the RNN to the training set
regressor.fit(x=x_train,
              y=y_train,
              epochs=100,
              batch_size=16)
filestring = ('/Users/admin/Documents/ASXdata/Result_Images/' +
              stock + '_' + 
              str(rolling_window) + '_' +
              str(hidden_layers)+'layers_' +
              str(layer_units[0])+'nodes_' +
              str(dropout_rate)+'dropout' + '.h5')
              
regressor.save(filestring)
print('Network model saved.')


##############################################################################
# PART 3: Making predictions and Visualization
##############################################################################
print("Training complete, beginning visualization.")
# importing the data
testing_set = dataImport(path, folder_string = 'week*/*')
real_stock_price = testing_set.iloc[:,4] # we save the real price for plotting purposes

dataset_total = pd.concat((training_set.iloc[:,:], testing_set.iloc[:,:]), axis = 0)
dataset_total = sc.transform(dataset_total)
inputs = dataset_total[len(dataset_total) - len(testing_set) - rolling_window:]

X_test = []
testarray = []
for i in range(rolling_window, len(inputs)):
    X_test.append(inputs[i-rolling_window:i, :4])
    testarray.append(inputs[i, :]) 
    # testarray holds all the columns due to feature scaler requiring 5 dims
    # for inversion

X_test = np.array(X_test)
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 4))
testarray = np.array(testarray)

regressor = load_model(filestring)
scaled_predicted_stock_price = regressor.predict(X_test)
testarray[:,4] = scaled_predicted_stock_price[:,0] # we replace the column with our predictions
predicted_stock_price = sc.inverse_transform(testarray)
predicted_stock_price = predicted_stock_price[:,4]

# Visualising the results
plt.plot(real_stock_price, color = 'red', label = 'Real '+ stock + ' Price')
plt.plot(predicted_stock_price, color = 'blue', label = 'Predicted '+ stock + ' Price')
plt.title(stock + ' Stock Price Prediction')
plt.xlabel('Time')
plt.ylabel(stock + ' Stock Price')
plt.legend()
fig1 = plt.gcf()
fig1.savefig(filestring+'.png')
plt.show()
