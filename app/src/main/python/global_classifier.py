import argparse
import os
import sys
import io
import torch
from os.path import dirname, join
from PIL import Image
import torchvision.transforms as transforms

from networks.drn_seg import DRNSub
from utils.tools import *
from utils.visualize import *
#from android.os import Environment


def load_classifier(model_path, gpu_id):
    if torch.cuda.is_available() and gpu_id != -1:
        device = 'cuda:{}'.format(gpu_id)
    else:
        device = 'cpu'
    model = DRNSub(1)
    state_dict = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state_dict['model'])
    model.to(device)
    model.device = device
    model.eval()
    return model


tf = transforms.Compose([transforms.ToTensor(),
                         transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                              std=[0.229, 0.224, 0.225])])
def classify_fake(modelpth, img_path, no_crop=False,
                  model_file='utils/dlib_face_detector/mmod_human_face_detector.dat'):
    # Data preprocessing
    img_path = np.array(img_path)
    print(img_path)
    im_w, im_h = Image.open(io.BytesIO(img_path)).size
    if no_crop:
        face = Image.open(io.BytesOP(img_path)).convert('RGB')
    else:
        faces = face_detection(img_path, verbose=False, model_file=model_file)
        if len(faces) == 0:
            print("no face detected by dlib, exiting")
            return "-1"
            #sys.exit()
        print("face detected, proceeding with prediction")
        face, box = faces[0]
    print("loading up model and starting evaluation")
    #modelpath = join(dirname(__file__), "weights/global.pth")
    #model = join(dirname(__file__), "weights/global.pth")
    #the argument passed from Java doesn't target the model correctly, so it's hardcoded here (8/11/2020, and I don't know what I meant here)
    #modelpath = io.BytesIO(model)
    model = load_classifier(io.BytesIO(modelpth), 0)
    face = resize_shorter_side(face, 400)[0]
    face_tens = tf(face).to(model.device)

    # Prediction
    with torch.no_grad():
        prob = model(face_tens.unsqueeze(0))[0].sigmoid().cpu().item()
    #return prob
    return prob*100


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path", required=True, help="the model input")
    parser.add_argument(
        "--model_path", required=True, help="path to the drn model")
    parser.add_argument(
        "--gpu_id", default='0', help="the id of the gpu to run model on")
    parser.add_argument(
        "--no_crop",
        action="store_true",
        help="do not use a face detector, instead run on the full input image")
    args = parser.parse_args()

    model = load_classifier(args.model_path, args.gpu_id)
    prob = classify_fake(model, args.input_path, args.no_crop)
    print("Probibility being modified by Photoshop FAL: {:.2f}%".format(prob*100))
