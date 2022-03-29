import json
from sklearn.model_selection import train_test_split
import cv2
import random
from SymbolClassifier.SymbCNN import SymbolCNN
import numpy as np
import os
import tensorflowjs as tfjs
from SymbolClassifier.configuration import Configuration
from description import SymbolClassifierDescription
import sys

class SymbDG:

    def split_data(fileList):
        print(f"\n ■ Number of images in the dataset: {len(fileList )-1}")
        aux = []
        [aux.append(k) for k in fileList.keys()]
        train, test = train_test_split(aux, test_size=0.2)
        test, val = train_test_split(test, test_size=0.5)

        train_dict = {name: fileList[f'{name}'] for name in train}
        val_dict = {name: fileList[f'{name}'] for name in val}
        test_dict = {name: fileList[f'{name}'] for name in test}
        
        return train_dict, val_dict, test_dict


    def parse_files(files: dict):

        X_pos = list() 
        X_glyph = list()
        Y_pos = list() 
        Y_glyph = list()

        if not files == None:
            for key in files:
                json_path = key
                img_path = files[key]
                with open(json_path) as json_file:
                    data = json.load(json_file)
                    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    if 'pages' in data:
                        pages = data['pages']
                        for p in pages:
                            if 'regions' in p:
                                regions = p['regions']
                                for r in regions:
                                    # Stave coords
                                    top_r, _, bottom_r, _ = r['bounding_box']['fromY'], \
                                                            r['bounding_box']['fromX'], \
                                                            r['bounding_box']['toY'],   \
                                                            r['bounding_box']['toX']
                                    if 'symbols' in r:
                                        symbols = r['symbols']
                                        if len(symbols) > 0:
                                            for s in symbols:
                                                if 'bounding_box' in s:
                                                    # Symbol coords
                                                    top_s, left_s, bottom_s, right_s = s['bounding_box']['fromY'], \
                                                                                       s['bounding_box']['fromX'], \
                                                                                       s['bounding_box']['toY'],   \
                                                                                       s['bounding_box']['toX']
                                                    if 'agnostic_symbol_type' in s: 
                                                        if 'position_in_staff' in s:
                                                            # Symbol type and position
                                                            type_s = s['agnostic_symbol_type']
                                                            pos_s = s['position_in_staff']

                                                            if (bottom_s - top_s) != 0 and (right_s - left_s) != 0:
                                                                if (bottom_r - top_r) != 0 and (right_s - left_s) != 0:
                                                                    X_glyph.append(img[top_s:bottom_s, left_s:right_s])
                                                                    Y_glyph.append(type_s)
                                                                    X_pos.append(img[top_r:bottom_r, left_s:right_s])
                                                                    Y_pos.append(pos_s)

        Y_glyph_cats = set(Y_glyph)
        Y_pos_cats = set(Y_pos)
        print(f"{len(X_glyph)} symbols loaded with {len(Y_glyph_cats)} different types and {len(Y_pos_cats)} different positions.\n")

        return X_glyph, X_pos, Y_glyph, Y_pos, Y_glyph_cats, Y_pos_cats


    def printCV2(X, window_name='sample'):
        
        cv2.imshow(window_name, X)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def resize_glyph(image):
        # Normalizing images
        height = Configuration.img_height_g
        width = Configuration.img_width_g
        img = cv2.resize(image, (width, height)) / 255
        return img

    def resize_pos(image):
        # Normalizing images
        height = Configuration.img_height_p
        width = Configuration.img_width_p
        img = cv2.resize(image, (width, height))/255
        return img


    def batchCreator(batch_size, X_g, X_p, Y_g, Y_p, w2i_g, w2i_p):

        while True:
            
            for f in range(batch_size):
                idx = random.randint(0,len(X_g)-1)


                if f == 0:
                    input_g = np.expand_dims(SymbDG.resize_glyph(X_g[idx]), axis=0)
                    input_p = np.expand_dims(SymbDG.resize_pos(X_p[idx]), axis=0)
                    output_g = np.expand_dims(w2i_g[Y_g[idx]], axis=0)
                    output_p = np.expand_dims(w2i_p[Y_p[idx]], axis=0)
                else:
                    input_g = np.concatenate((input_g, np.expand_dims(SymbDG.resize_glyph(X_g[idx]), axis=0)), axis=0)
                    input_p = np.concatenate((input_p, np.expand_dims(SymbDG.resize_pos(X_p[idx]), axis=0)), axis=0)
                    output_g = np.concatenate((output_g, np.expand_dims(w2i_g[Y_g[idx]], axis=0)), axis=0)
                    output_p = np.concatenate((output_p, np.expand_dims(w2i_p[Y_p[idx]], axis=0)), axis=0)
                
            yield (input_g, input_p), (output_g, output_p)

    def save_dict(name, data):

        if not os.path.exists('./MuRETPackage/SymbolClassifier'):
            os.mkdir('./MuRETPackage/SymbolClassifier')
        
        with open(f'./MuRETPackage/SymbolClassifier/{name}.json', 'w') as fp:
            json.dump(data, fp, indent=4)

    def createVocabs(glyphs, positions):
        w2i_glyphs_vocab = {i: idx for idx, i in enumerate(glyphs)}
        w2i_pos_vocab    = {i: idx for idx, i in enumerate(positions)}

        i2w_glyphs_vocab = {w2i_glyphs_vocab[i] : i for i in w2i_glyphs_vocab}
        i2w_pos_vocab    = {w2i_pos_vocab[i]    : i for i in w2i_pos_vocab}

        SymbDG.save_dict('w2i_glyphs', w2i_glyphs_vocab)
        SymbDG.save_dict('w2i_pos', w2i_pos_vocab)
        SymbDG.save_dict('i2w_glyphs', i2w_glyphs_vocab)
        SymbDG.save_dict('i2w_pos', i2w_pos_vocab)

        return w2i_glyphs_vocab, w2i_pos_vocab, i2w_glyphs_vocab, i2w_pos_vocab
        

    def main(fileList: dict, args):

        batch_size = 32

        train_dict, val_dict, test_dict = SymbDG.split_data(fileList)

        X_g, X_p, Y_g, Y_p, Y_g_cats, Y_p_cats = SymbDG.parse_files(train_dict)

        w2i_g, w2i_p, i2w_g, i2w_p = SymbDG.createVocabs(Y_g_cats, Y_p_cats)

        generator = SymbDG.batchCreator(batch_size, X_g, X_p, Y_g, Y_p, w2i_g, w2i_p)

        description = SymbolClassifierDescription('SymbolClassifier', None, Configuration.img_height_g, Configuration.img_width_g,
                                                batch_size, fileList)

        description.i2w_g = i2w_g
        description.w2i_g = w2i_g
        description.i2w_p = i2w_p
        description.w2i_p = w2i_p
        description.input_h_2 = Configuration.img_height_p
        description.input_w_2 = Configuration.img_width_p

        
        # [ 
        #   [[img_glyph , img_pos ]] ,
        #   [[gt_glyph  , gt_pos  ]] 
        # ]


        model = SymbolCNN.model(len(Y_g_cats), len(Y_p_cats))
        steps = len(X_g)//batch_size

        print('\n=== Starting training process ===\n')
        #model.fit(generator,
        #        steps_per_epoch=steps,
        #        epochs=15,
        #        verbose=1)
        epochs = 15

        description.model_epochs = epochs
        description.save_description()

        #sys.exit(-1)

        model.fit(generator,
                steps_per_epoch=1,
                epochs=1,
                verbose=1)

        if args.h5:
            model.save(f'./MuRETPackage/SymbolClassifier/SymbolClassifier.h5')
        SymbolClassifier = model
        tfjs.converters.save_keras_model(SymbolClassifier, './MuRETPackage/SymbolClassifier/tfjs/')

if __name__ == '__main__':
    SymbDG.main()