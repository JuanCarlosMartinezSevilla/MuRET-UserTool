from pyexpat import model
from CRNN.data import DataGenerator
from CRNN.model import get_model
from CRNN.evaluator import ModelEvaluator
from CRNN.utils_crnn import UtilsCRNN as U
import argparse
import logging
import itertools
import tqdm
from sklearn.model_selection import train_test_split
#import tensorflowjs as tfjs

def split_data(fileList):
    print("\n=== Number of images ===")
    print(len(fileList))
    aux = []
    [aux.append(k) for k in fileList.keys()]
    train, test = train_test_split(aux, test_size=0.2)
    test, val = train_test_split(test, test_size=0.5)

    train_dict = {name: fileList[f'{name}'] for name in train}
    val_dict = {name: fileList[f'{name}'] for name in val}
    test_dict = {name: fileList[f'{name}'] for name in test}
    
    return train_dict, val_dict, test_dict

def main(args, fileList, ligatures):

    fileList = U.clean_data(fileList)
    

    train_dict, val_dict, test_dict = split_data(fileList)
    ##TODO maybe we are getting json without ligatures on it

    #print(fileList)
    print("\n=== Train data ===")
    dg = DataGenerator(dataset_list_path=train_dict,
                       aug_factor=3, # seq (1 5)
                       batch_size=8,
                       num_channels=3,
                       width_reduction=8, ligatures=ligatures)


    model_tr, model_pr = get_model(vocabulary_size=len(dg.w2i))

    #X_val, Y_val, _, _ = U.parse_lst(args.validation)
    #fileList = dict(itertools.islice(fileList.items(), 4))
    if ligatures:
        print("\n=== Validation data ===")
        X_val, Y_val, _, _ = U.parse_lst_dict_ligatures(val_dict)
    else:
        X_val, Y_val, _, _ = U.parse_lst_dict(val_dict)
    #evaluator_val = ModelEvaluator([X_val, Y_val], aug_factor=args.aug_test)
    evaluator_val = ModelEvaluator([X_val, Y_val], aug_factor=0)

    #X_test, Y_test, _, _ = U.parse_lst(args.test)
    if ligatures:
        print("\n=== Test data ===")
        X_test, Y_test, _, _ = U.parse_lst_dict_ligatures(test_dict)
    else:
        X_test, Y_test, _, _ = U.parse_lst_dict(test_dict)
    #evaluator_test = ModelEvaluator([X_test, Y_test], aug_factor=args.aug_test)
    evaluator_test = ModelEvaluator([X_test, Y_test], aug_factor=0)

    #if args.model:
    #    best_ser_val = 100
    best_ser_val = 100

    for super_epoch in range(1000):
        print("Epoch {}".format(super_epoch))
        model_tr.fit(dg,
                     steps_per_epoch=100,
                     epochs=1,
                     verbose=1)

        print(f"\tEvaluating...\tBest SER val: {best_ser_val:.2f}")
        ser_val = evaluator_val.eval(model_pr, dg.i2w)
        ser_test = evaluator_test.eval(model_pr, dg.i2w)
        print("\tEpoch {}\tSER_val: {:.2f}\tSER_test: {:.2f}".format(super_epoch, ser_val, ser_test))

        #if args.model:
        if ser_val < best_ser_val:
            print("\tSER improved from {} to {} --> Saving model.".format(best_ser_val, ser_val))
            best_ser_val = ser_val
            #model_pr.save_weights("model_weights.h5")
            if ligatures:
                model_pr.save(f'./MuRETPackage/EndToEnd/EndToEndLigatures.h5')
                # Save model to use it with tensorflow.js
                EndToEndLigatures = model_pr
                #tfjs.converters.save_keras_model(EndToEndLigatures, './MuRETPackage/EndToEnd/')
            else:
                model_pr.save(f'./MuRETPackage/EndToEnd/EndToEnd.h5')
                EndToEnd = model_pr
                #tfjs.converters.save_keras_model(EndToEnd, './MuRETPackage/EndToEnd/')


def build_argument_parser():

    #python -u experiment.py -tr /media/jcalvo/Data/Datasets/MuRET/5-CV/Capitan/train_gt_fold$f.dat  -val /media/jcalvo/Data/Datasets/MuRET/5-CV/Capitan/val_gt_fold$f.dat -ts /media/jcalvo/Data/Datasets/MuRET/5-CV/Capitan/test_gt_fold$f.dat -a $a -b $b -f $fusion > LOG_$f-$fusion-$a-$b.log

    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-tr', '--train', action='store', required=True,
                        help='List of training samples.')
    parser.add_argument('-val', '--validation', action='store', required=True,
                        help='List of validation samples.')
    parser.add_argument('-ts', '--test', action='store', required=True,
                        help='List of test samples.')
    parser.add_argument('-a', '--aug_train', action='store', required=True,
                        type=int,
                        help='Augmentation factor during training.')
    parser.add_argument('-b', '--aug_test', action='store', required=True,
                        type=int,
                        help='Augmentation factor during validation and test.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Turn on DEBUG messages.')
    parser.add_argument('-m', '--model', action='store_true',
                        help='Turn on saving best validation model.')
    return parser


if __name__ == '__main__':

    parser = build_argument_parser()
    args = parser.parse_args()

    print(args)

    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)
