from ast import Store
from utils import Utils
from DataAugmentation.file_manager import FileManager
import shutil
import os
import argparse
from pathlib import Path
import errno

class Main:

    def seeDir(aux_path):
        
        path_to_download_images = './dataset'
        aux_path = args.path

        # To not retrieve the images again
        if args.reload:

            if not os.path.exists('./MuRETPackage'):
                os.mkdir('./MuRETPackage')

            if os.path.exists(path_to_download_images):
                shutil.rmtree(path_to_download_images)
                os.mkdir(path_to_download_images)
            else:
                os.mkdir(path_to_download_images)

            ## IF WE GET THE .TGZ AUTO FROM
            #files = FileManager.listFiles('./')
            #for f in files:
            #    if f.split('.')[-1] == 'tgz':
            #        file = f
            #        break
            #
            #file = os.path.join('./', file)
            #print(file)

            if os.path.exists(aux_path):

                Utils.decompressFile(aux_path, path_to_download_images)
                fileList = FileManager.listFilesRecursive(path_to_download_images)

                Utils.readJSONGetImagesFromUrl(fileList, path_to_download_images)
            else:
                raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), aux_path.split('/')[-1])
            
        fileList = FileManager.listFilesRecursive(path_to_download_images)
        fileList = FileManager.createRoutesDict(fileList)
        return fileList

    def local_main(args):

        fileList = Main.seeDir(args)

        
        if args.doc_analysis:
            print("doc_analysis")
            Utils.callDataAug(1)
            Utils.callSAE(fileList)

        if args.end_to_end:
            #Utils.createStavesDataset(fileList)
            # Launch E2E
            Utils.callE2E(fileList)
            print("e2e")
        
        if args.end_to_end_ligatures:
            Utils.callE2ELigatures(fileList)
            
        if args.symb_classifier:
            #Utils.createSymbolsDataset(fileList)
            # Launch Symbol Classifier
            print("symbol_classifier")
        

    def ligatures(args):
        fileList = Main.seeDir(args, aux_path = './ligaturesDataset')
        Utils.callE2ELigatures(fileList)

    def validate_file(f):
        if not os.path.exists(f):
            # Argparse uses the ArgumentTypeError to give a rejection message like:
            # error: argument input: x does not exist
            raise argparse.ArgumentTypeError("{0} does not exist".format(f))
        return f

    def argument_parser():
        parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                            formatter_class=argparse.RawDescriptionHelpFormatter)

        #parser.add_argument('-p', '--path', action='store', required=True,
        #                        help='Path to dataset .tgz file.')
        parser.add_argument("-p", "--path", required=True, type=Main.validate_file,
                        help="Path to dataset .tgz file.")
        parser.add_argument('-da', '--doc_analysis', action='store_true',
                                help='Train a document analysis model.')
        parser.add_argument('-e2e', '--end_to_end', action='store_true',
                                help='Train an agnostic end to end model.')
        parser.add_argument('-e2el', '--end_to_end_ligatures', action='store_true',
                                help='Train an agnostic end to end model for ligatures recognition.')
        parser.add_argument('-sc', '--symb_classifier', action='store_true',
                                help='Train a symbol classifier model.')
        parser.add_argument('-rl', '--reload', action='store_true',
                                help='Reload dataset.')

        return parser

if __name__ == '__main__':


    parser = Main.argument_parser()
    args = parser.parse_args()

    print(args)



    #args = [NewDatasetLoad, DocumentAnalysis, E2E, SymbolAnalysis, HeightAnalysis]
    Main.local_main(args)
    #Main.ligatures(args)
