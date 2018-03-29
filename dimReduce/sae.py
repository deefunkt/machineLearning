# -*- coding: utf-8 -*-

# TODO: import and convert train+test data
# TODO: generalize for minibatch training

# Importing the libraries
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.optim as optim
import torch.utils.data
from torch.autograd import Variable

# Need to define the datasets to be modelled
training_set = torch.FloatTensor(training_set)
test_set = torch.FloatTensor(test_set)

# This class defines the stacked autoencoder object
# composed of an encoding stage and a decoding stage
# use the output to the encoding stage for dimensionality reduction
class SAE(nn.Module):
    def __init__(self, ):
        super(SAE, self).__init__()
        self.fc1 = nn.Linear(nb_movies, 20)
        self.fc2 = nn.Linear(20, 10)
        self.fc3 = nn.Linear(10, 20)
        self.fc4 = nn.Linear(20, nb_movies)
        self.activation = nn.Sigmoid()
    def forward(self, x):        
        encoded = self.encode(x)
        decoded = self.decode(encoded)
        return decoded
    def encode(self, x):
        x = self.activation(self.fc1(x))
        x = self.activation(self.fc2(x))
        return x
    def decode(self, x):
        x = self.activation(self.fc3(x))
        x = self.fc4(x)
        return x
    
sae = SAE()
criterion = nn.MSELoss()

# Training the SAE
nb_epoch = 200
for epoch in range(1, nb_epoch + 1):
    # experimenting with decaying learning rate. Perhaps more epochs needed.
    optimizer = optim.RMSprop(sae.parameters(), lr = 0.05/(epoch/2), weight_decay = 0.5)
    train_loss = 0
    s = 0.
    for entry in training_set:
        input = Variable(entry).unsqueeze(0) # for compatibility with Torch.
        target = input.clone()
        target.require_grad = False
        if torch.sum(target.data > 0) > 0: # as long as the target data isnt empty
            encoded_input = sae.encode(input)
            output = sae.decode(encoded_input)
            loss = criterion(output, target)
            loss.backward()
            train_loss += np.sqrt(loss.data[0])
            s += 1.
            optimizer.step()
    print('epoch: '+str(epoch)+' loss: '+str(train_loss/s))