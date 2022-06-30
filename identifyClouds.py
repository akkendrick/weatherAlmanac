import numpy as np
import os
import sys
import PIL
import tensorflow as tf
import pathlib
import matplotlib.pyplot as plt

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

import datetime
from subprocess import call

batch_size = 32
img_height = 180
img_width = 180

def loadTimeStamp():
  # Format time stamp for 3 pm
  now = datetime.datetime.now()
  date_time = now.strftime("%Y%m%d")
  date_timeHR = date_time+'150000'
  dataDirectory = '/data/toIDFiles/' 
  workingDirectory = os.getcwd()
  files = os.listdir(workingDirectory+dataDirectory)
  
  diff = []
  for file in files:
    partFile = int(file[6:-4])
    diff.append([partFile - int(date_timeHR)])
  
  goodTime = np.argmin(np.abs(diff))
  print(goodTime)

  hostFile = files[goodTime]
  print(hostFile)
  return hostFile


def trainModel():
  myFile = 'data.tar.gz' # Path to images, .tar.gz is fine with the untar option below
  fullPath = os.path.abspath("./" + myFile)  # get full path for keras command
  data_dir = keras.utils.get_file(myFile, 'file://'+fullPath, untar=True)
  data_dir = pathlib.Path(data_dir)
  
  batch_size = 32
  img_height = 180
  img_width = 180

  # Training
  train_ds = tf.keras.utils.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size)

  # Validation
  val_ds = tf.keras.utils.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size)

  class_names = train_ds.class_names
  print(class_names)

  AUTOTUNE = tf.data.AUTOTUNE

  train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
  val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

  normalization_layer = layers.Rescaling(1./255)

  normalized_ds = train_ds.map(lambda x, y: (normalization_layer(x), y))
  image_batch, labels_batch = next(iter(normalized_ds))

  num_classes = len(class_names)

  model = Sequential([
    layers.Rescaling(1./255, input_shape=(img_height, img_width, 3)),
    layers.Conv2D(16, 3, padding='same', activation='relu'),
    layers.MaxPooling2D(),
    layers.Conv2D(32, 3, padding='same', activation='relu'),
    layers.MaxPooling2D(),
    layers.Conv2D(64, 3, padding='same', activation='relu'),
    layers.MaxPooling2D(),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(num_classes)
  ])

  model.compile(optimizer='adam',
                loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                metrics=['accuracy'])

  model.summary()

  epochs=5
  history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=epochs
  )

  return model, class_names



def identifyClouds(myFile, model, class_names):
  ################################################################
  # Predict on new
  #myFile = 'noCloud.jpg' # Path to images, .tar.gz is fine with the untar option below
  fullPath = os.path.abspath("./data/toIDFiles/" + myFile)  # get full path for keras command
  image_path = tf.keras.utils.get_file(myFile, origin='file://'+fullPath)

  img = tf.keras.utils.load_img(
      image_path, target_size=(img_height, img_width)
  )
  img_array = tf.keras.utils.img_to_array(img)
  img_array = tf.expand_dims(img_array, 0) # Create a batch

  predictions = model.predict(img_array)
  score = tf.nn.softmax(predictions[0])

  print(
      "This image most likely belongs to {} with a {:.2f} percent confidence."
      .format(class_names[np.argmax(score)], 100 * np.max(score))
  )
  return(class_names[np.argmax(score)])

if __name__ == '__main__':
  hostFile = loadTimeStamp()
  print(hostFile)

  model, class_names = trainModel()
  classID = identifyClouds(hostFile, model, class_names)
  print(classID)
