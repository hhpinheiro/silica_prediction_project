# -*- coding: utf-8 -*-
"""LSTM Tunning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1x3ShgcQEvmRdkPRNUjZGNEmUZUCi0GCU
"""

import os
import datetime

import IPython
import IPython.display
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf

from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn import metrics
from sklearn.model_selection import cross_validate
from sklearn.metrics import recall_score
from sklearn.model_selection import KFold

from tensorflow import keras
from tensorflow.keras import layers

print(tf.__version__)
!pip install -q git+https://github.com/tensorflow/docs
import tensorflow_docs as tfdocs
import tensorflow_docs.plots
import tensorflow_docs.modeling
# to get the id part of the file 

mpl.rcParams['figure.figsize'] = (8, 6)
mpl.rcParams['axes.grid'] = False


from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn import metrics
from sklearn.model_selection import cross_validate
from sklearn.metrics import recall_score
from sklearn.model_selection import KFold

# Authenticate and create the PyDrive client. 
from pydrive.auth import GoogleAuth 
from pydrive.drive import GoogleDrive 
from google.colab import auth 
from oauth2client.client import GoogleCredentials 
auth.authenticate_user() 
gauth = GoogleAuth() 
gauth.credentials = GoogleCredentials.get_application_default() 
drive = GoogleDrive(gauth)

id = '1FmocjGvyUReH1K0Yl-p8sBAZLarCA9GM'
  
downloaded = drive.CreateFile({'id':id})  
downloaded.GetContentFile('MiningProcess_Flotation_Plant_Database.csv')   

df = pd.read_csv('MiningProcess_Flotation_Plant_Database.csv', decimal=',', sep=',') 

df.head()

'''
Import the dataset, makes the average of the variables over a period of 1 hour,
extract the date from the df and save all features in a df variable. The date_time 
variable is already in a datetime format
'''

df = pd.read_csv('MiningProcess_Flotation_Plant_Database.csv', decimal=',', sep=',') 
df = df.set_index(['date'])
df.index = pd.to_datetime(df.index)
df = df.resample('60min').mean()
df.reset_index(inplace=True)
df = df.rename(columns = {'index':'date'})

df.dropna(inplace=True)

date_time = pd.to_datetime(df.pop('date'), format='%Y-%m-%d %H:%M:%S')
df = df.iloc[:,:]

timestamp_s = date_time.map(datetime.datetime.timestamp)

'''
Data splitting into train, validation and test datasets.
'''

column_indices = {name: i for i, name in enumerate(df.columns)}

n = len(df)
train_df = df[0:int(n*0.7)]
val_df = df[int(n*0.7):int(n*0.9)]
test_df = df[int(n*0.9):]

num_features = df.shape[1]

'''
Feature normalization
'''

train_stats = train_df.describe()
train_stats = train_stats.transpose()

def norm(x):
  return (x - train_stats['mean']) / train_stats['std']

train_df = norm(train_df)
val_df = norm(val_df)
test_df = norm(test_df)

class WindowGenerator():
  def __init__(self, input_width, label_width, shift,
               train_df=train_df, val_df=val_df, test_df=test_df,
               label_columns=None):
    # Store the raw data.
    self.train_df = train_df
    self.val_df = val_df
    self.test_df = test_df

    # Work out the label column indices.
    self.label_columns = label_columns
    if label_columns is not None:
      self.label_columns_indices = {name: i for i, name in
                                    enumerate(label_columns)}
    self.column_indices = {name: i for i, name in
                           enumerate(train_df.columns)}

    # Work out the window parameters.
    self.input_width = input_width
    self.label_width = label_width
    self.shift = shift

    self.total_window_size = input_width + shift

    self.input_slice = slice(0, input_width)
    self.input_indices = np.arange(self.total_window_size)[self.input_slice]

    self.label_start = self.total_window_size - self.label_width
    self.labels_slice = slice(self.label_start, None)
    self.label_indices = np.arange(self.total_window_size)[self.labels_slice]

  def __repr__(self):
    return '\n'.join([
        f'Total window size: {self.total_window_size}',
        f'Input indices: {self.input_indices}',
        f'Label indices: {self.label_indices}',
        f'Label column name(s): {self.label_columns}'])

w1 = WindowGenerator(input_width=24, label_width=1, shift=24,
                     label_columns=['% Silica Concentrate'])
w2 = WindowGenerator(input_width=24, label_width=1, shift=1,
                     label_columns=['% Silica Concentrate'])

def split_window(self, features):
  inputs = features[:, self.input_slice, :]
  labels = features[:, self.labels_slice, :]
  if self.label_columns is not None:
    labels = tf.stack(
        [labels[:, :, self.column_indices[name]] for name in self.label_columns],
        axis=-1)

  # Slicing doesn't preserve static shape information, so set the shapes
  # manually. This way the `tf.data.Datasets` are easier to inspect.
  inputs.set_shape([None, self.input_width, None])
  labels.set_shape([None, self.label_width, None])

  return inputs, labels

WindowGenerator.split_window = split_window

# Stack three slices, the length of the total window:
example_window = tf.stack([np.array(train_df[:w2.total_window_size]),
                           np.array(train_df[100:100+w2.total_window_size]),
                           np.array(train_df[300:300+w2.total_window_size])])


example_inputs, example_labels = w2.split_window(example_window)

print('All shapes are: (batch, time, features)')
print(f'Window shape: {example_window.shape}')
print(f'Inputs shape: {example_inputs.shape}')
print(f'labels shape: {example_labels.shape}')

def plot(self, model=None, plot_col='% Silica Concentrate', max_subplots=3):
  inputs, labels = self.example
  plt.figure(figsize=(12, 8))
  plot_col_index = self.column_indices[plot_col]
  max_n = min(max_subplots, len(inputs))
  for n in range(max_n):
    plt.subplot(3, 1, n+1)
    plt.ylabel(f'{plot_col} [normed]')
    plt.plot(self.input_indices, inputs[n, :, plot_col_index],
             label='Inputs', marker='.', zorder=-10)

    if self.label_columns:
      label_col_index = self.label_columns_indices.get(plot_col, None)
    else:
      label_col_index = plot_col_index

    if label_col_index is None:
      continue

    plt.scatter(self.label_indices, labels[n, :, label_col_index],
                edgecolors='k', label='Labels', c='#2ca02c', s=64)
    if model is not None:
      predictions = model(inputs)
      plt.scatter(self.label_indices, predictions[n, :, label_col_index],
                  marker='X', edgecolors='k', label='Predictions',
                  c='#ff7f0e', s=64)

    if n == 0:
      plt.legend()

  plt.xlabel('Time [h]')

WindowGenerator.plot = plot

w2.example = example_inputs, example_labels
w2.plot()

def make_dataset(self, data):
  data = np.array(data, dtype=np.float32)
  ds = tf.keras.preprocessing.timeseries_dataset_from_array(
      data=data,
      targets=None,
      sequence_length=self.total_window_size,
      sequence_stride=1,
      shuffle=True,
      batch_size=32,)

  ds = ds.map(self.split_window)

  return ds

WindowGenerator.make_dataset = make_dataset

@property
def train(self):
  return self.make_dataset(self.train_df)

@property
def val(self):
  return self.make_dataset(self.val_df)

@property
def test(self):
  return self.make_dataset(self.test_df)

@property
def example(self):
  """Get and cache an example batch of `inputs, labels` for plotting."""
  result = getattr(self, '_example', None)
  if result is None:
    # No example batch was found, so get one from the `.train` dataset
    result = next(iter(self.train))
    # And cache it for next time
    self._example = result
  return result

WindowGenerator.train = train
WindowGenerator.val = val
WindowGenerator.test = test
WindowGenerator.example = example

"""Single step-prediction"""

single_step_window = WindowGenerator(
    input_width=1, label_width=1, shift=1,
    label_columns=['% Silica Concentrate'])
single_step_window

wide_window = WindowGenerator(
    input_width=100, label_width=100, shift=1,
    label_columns=['% Silica Concentrate'])

lstm_units = [8, 16, 32, 64, 128, 256, 512]
dense_units = [8, 16, 32, 64, 128, 256, 512]
dropout_rate = [0.2, 0.3, 0.4, 0.5]

MAX_EPOCHS = 30

def compile_and_fit(model, window, patience=2):
  early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', patience=5)

  model.compile(loss=tf.losses.MeanSquaredError(),
                optimizer=tf.optimizers.Adam(),
                metrics=['mae', 'mse'])

  history = model.fit(window.train, epochs=MAX_EPOCHS,
                      validation_data=window.val,
                      verbose = 2,
                      callbacks=[early_stopping, tfdocs.modeling.EpochDots()])
  return history

for i in lstm_units:
  for j in dense_units:
    for k in dropout_rate:
      print("========================================== LSTM units = ", i,  "dense_units = ", j, "dropout_rate = ", k, '========================================== ')

      single_step_lstm = tf.keras.models.Sequential([
          tf.keras.layers.LSTM(i, return_sequences=True),
          tf.keras.layers.Dropout(k),
          tf.keras.layers.Dense(j, activation = 'relu'),
          tf.keras.layers.Dropout(k),
          tf.keras.layers.Dense(1)
      ])

      history = compile_and_fit(single_step_lstm, single_step_window)
      '''
      wide_window.plot(single_step_lstm)
      
      plotter = tfdocs.plots.HistoryPlotter(smoothing_std=2)
      plotter.plot({'Early Stopping': history}, metric = "mae")
      plt.ylim([0.2, 0.65])
      plt.ylabel('MAE [%Silica Concentrate]')

      '''
      print(" ") 
      print(" ")

"""MULTI STEP MODELS

"""

OUT_STEPS = 24
multi_window = WindowGenerator(input_width=24,
                               label_width=OUT_STEPS,
                               shift=OUT_STEPS)

multi_window.plot()
multi_window

multi_step_lstm = tf.keras.models.Sequential([
    tf.keras.layers.LSTM(64, return_sequences=True),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(64, activation = 'relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(1)
])
history = compile_and_fit(multi_step_lstm, multi_window)

IPython.display.clear_output()

multi_window.plot(multi_step_lstm)

plotter = tfdocs.plots.HistoryPlotter(smoothing_std=2)
plotter.plot({'Early Stopping': history}, metric = "mae")
plt.ylim([0.2, 0.65])
plt.ylabel('MAE [%Silica Concentrate]')

