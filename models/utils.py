import numpy as np
from PIL import Image
import os
import random

def build_dataset(numImages,trainingSplit,imageBaseDir="../training_data/images/",positiveSplit=0.5):
    
    # Get the number of negative and positive images
    numPositiveImages = int(numImages*positiveSplit)
    numNegativeImages = numImages-numPositiveImages

    # Get a list of file names
    positiveImageFileList = [fileName for fileName in os.listdir(imageBaseDir+"positive/") if fileName.endswith("png")][:numPositiveImages]
    positiveImageFileList = [imageBaseDir+"positive/"+fileName for fileName in positiveImageFileList]
    negativeImageFileList = [fileName for fileName in os.listdir(imageBaseDir+"negative/") if fileName.endswith("png")][:numNegativeImages]
    negativeImageFileList = [imageBaseDir+"negative/"+fileName for fileName in negativeImageFileList if fileName.endswith("png")]

    # Loop through and get all of the positive examples
    positiveList = []
    for positiveImageFile in positiveImageFileList:
        positiveList.append([positiveImageFile,1])

    # Loop through and get all of the negative examples
    negativeList = []
    for negativeImageFile in negativeImageFileList:
        negativeList.append([negativeImageFile,0])

    # Put the list together and shuffle the list
    fullList = positiveList+negativeList
    random.shuffle(fullList)

    # Get the number of training/test samples
    numTrainImages = int(numImages*trainingSplit)
    numTestImages = numImages-numTrainImages

    # Get the samples corresponding to the training/testing split
    trainSampleList = fullList[:numTrainImages]
    testSampleList = fullList[-numTestImages:]
    
    # Split off x and y for the training and testing sets
    xTrainList = [trainSample[0] for trainSample in trainSampleList]
    yTrainList = [trainSample[1] for trainSample in trainSampleList]
    xTestList = [testSample[0] for testSample in testSampleList]
    yTestList = [testSample[1] for testSample in testSampleList]
    
    return xTrainList, yTrainList, xTestList, yTestList

def load_data(xList,yList):
    
    # Loop through the path and load the images
    X = []
    for x in xList:
        
        # Read the image
        image = Image.open(x)
        X.append(np.asarray(image)[:,:,0]/255.)
        
    # Reshape the example data
    X = np.asarray(X,dtype=np.float32)
    X = X.reshape(X.shape[0],X.shape[1],X.shape[2],1)

    # Cast lists to arrays of the proper size
    Y = np.asarray(yList,dtype=np.float32)
        
    return X,Y

def normalize_samples(x):
    
    # Get normalization parameters
    mu = x.mean()
    sigma = x.std()
    
    return mu,sigma,(x-mu)/sigma