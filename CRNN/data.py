import numpy as np
from CRNN.config import Config
from CRNN.utils_crnn import UtilsCRNN as U
import random
import cv2
import json


def chooseRandomImageFromFolder(listOfFiles):
    for file in random.choice(listOfFiles):
        cv2.imread(file)


class DataGenerator:

    def __init__(self, dataset_list_path, aug_factor, width_reduction, num_channels, batch_size, ligatures, w2i, i2w):
        self.ligatures = ligatures
        #print(dataset_list_path)
        #dataset_list_path = dict(itertools.islice(dataset_list_path.items(), 4))
        self.i2w = i2w
        self.w2i = w2i
        self.X = dataset_list_path
        self.aug_factor = aug_factor
        self.batch_size = batch_size
        self.width_reduction = width_reduction
        self.num_channels = num_channels
        self.idx = 0
        

    def __iter__(self):
        return self

    def __next__(self):
        X_batch = []
        Y_batch = []

        max_image_width = 0
        for _ in range(self.batch_size):

            # aug factor == 0 means no augmentation at all
            #print(self.idx)

            ### Seleccionar imagen de random de /dataset/e2e_crops
            name = self.X[self.idx]
            sample_image = cv2.imread(f'./dataset_crops/e2e_crops/{name}', cv2.IMREAD_COLOR)
            sample_image = U.normalize(sample_image)
            sample_image = U.resize(sample_image, Config.img_height)
            max_image_width = max(max_image_width, sample_image.shape[1])

            X_batch.append(sample_image)
            with open(f'./dataset_crops/e2e_crops/{name.replace("png", "json")}') as json_file:
                data = json.load(json_file)
            Y_batch.append([self.w2i[symbol] for symbol in data["info"]])
            self.idx = (self.idx + 1) % len(self.X)

        X_train = np.zeros(
            shape=[self.batch_size, Config.img_height, max_image_width, self.num_channels],
            dtype=np.float32)
        L_train = np.zeros(shape=[len(X_batch), 1])

        for i, sample in enumerate(X_batch):
            X_train[i, 0:sample.shape[0], 0:sample.shape[1]] = sample
            L_train[i] = sample.shape[1] // self.width_reduction  # width_reduction from CRNN

        # Y_train, T_train
        max_length_seq = max([len(w) for w in Y_batch])

        Y_train = np.zeros(shape=[len(X_batch), max_length_seq])
        T_train = np.zeros(shape=[len(X_batch), 1])
        for i, seq in enumerate(Y_batch):
            Y_train[i, 0:len(seq)] = seq
            T_train[i] = len(seq)

        return [X_train, Y_train, L_train, T_train], np.zeros((X_train.shape[0], 1), dtype='float16')


if __name__ == "__main__":
    """
    dg = DataGenerator(dataset_list_path='/media/jcalvo/Data/Datasets/MuRET/b59850.lst',
                       aug_factor=3,
                       batch_size=8,
                       num_channels=3,
                       width_reduction=8)

    [x,y,l,t], o = next(dg)

    print(x.shape)
    print(y.shape)
    print(y)
    print(l.shape)
    print(l)
    print(t.shape)
    print(t)
    """
