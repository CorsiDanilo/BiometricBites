import os
import cv2
import pickle
import tensorflow as tf
import numpy as np
from PIL import Image
from bsproject.paths import SAMPLES_ROOT, LABELS_ROOT, MODELS_ROOT
from abc import ABC, abstractmethod


class Classifier(ABC):
    """
    Abstract class, this shouldn't be instanced, but it describes the common fields and methods that a classifier have.
    """
    def __init__(self) -> None:
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.side_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        self.image_dir = SAMPLES_ROOT
        self.models_root = MODELS_ROOT
        self.labels_root = LABELS_ROOT
        self.image_width = 224
        self.image_height = 224
        self.create_necessary_folders()
    
    @abstractmethod
    def recognize(self, frame: str):
        pass
    
    @abstractmethod
    def train(self):
        pass

    def create_necessary_folders(self):
        """
        It creates labels and models folders if they don't already exist.
        """
        if not os.path.exists(self.labels_root):
            os.makedirs(self.labels_root)
        if not os.path.exists(self.models_root):
            os.makedirs(self.models_root)

    def is_image_preprocessed(self, file_name):
        """
        Check if the image is already preprocessed.
        """
        return "processed" in file_name
    
    def draw_label(self, frame, label, x, y):
        """
        Draw the predicted lable on the frame.
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (255, 255, 255)
        stroke = 2
        cv2.putText(frame, label, (x,y), font, 1, color, stroke, cv2.LINE_AA)
        return frame

    def preprocess_images(self):
        """
        Detect frontal and profile faces inside the image, crops them and saves them in the same directory, deleting the original images.
        If the image is already preprocessed, it is skipped.
        """
        image_width = self.image_width
        image_height = self.image_height

        # for detecting faces
        frontal_face_cascade = self.face_cascade
        side_face_cascade = self.side_face_cascade

        current_id = 0
        label_ids = {}

        # iterates through all the files in each subdirectories
        for root, _, files in os.walk(self.image_dir):
            for file in files:
                if self.is_image_preprocessed(file):
                    print(f"---Photo {file} skipped because it is already preprocessed---\n")
                    continue
                # path of the image
                path = os.path.join(root, file)

                # get the label name (name of the person)
                label = os.path.basename(root).replace(" ", ".").lower()

                # add the label (key) and its number (value)
                if not label in label_ids:
                    label_ids[label] = current_id
                    current_id += 1

                # load the image
                imgtest = cv2.imread(path, cv2.IMREAD_COLOR)
                try:
                    img_gray = cv2.cvtColor(imgtest, cv2.COLOR_BGR2GRAY)
                except:
                    print(f"---Photo {file} skipped because there is no face---\n")
                    continue
                image_array = np.array(imgtest, "uint8")

                # get the faces detected in the image
                frontal_faces = frontal_face_cascade.detectMultiScale(img_gray, scaleFactor=1.1, minNeighbors=5)
                profile_faces = np.array([])

                if len(frontal_faces) == 0:
                    profile_faces = side_face_cascade.detectMultiScale(img_gray, scaleFactor=1.1, minNeighbors=5)
                    if len(profile_faces) == 0:
                        print(f"---Photo {file} skipped because it doesn't contain any face---\n")
                        os.remove(path)
                        continue
                    else:
                        faces = profile_faces
                else:
                    faces = frontal_faces
                
                # save the detected face(s) and associate
                # them with the label
                for (x_, y_, w, h) in faces:
                    # resize the detected face to 224x224
                    size = (image_width, image_height)

                    # detected face region
                    roi = image_array[y_: y_ + h, x_: x_ + w]

                    # resize the detected head to target size
                    resized_image = cv2.resize(roi, size)
                    image_array = np.array(resized_image, "uint8")

                    # remove the original image
                    if os.path.exists(path): os.remove(path)

                    # replace the image with only the face
                    im = Image.fromarray(image_array)
                    new_file_name = f"{file.split('.')[0]}_processed.jpg"
                    new_path = os.path.join(root, new_file_name)
                    im.save(new_path)          
                
    def detect_faces(self, frame):
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        face_present = len(faces) != 0
        if not face_present:
            return frame, frame, False
        for (x_, y_, w, h) in faces:
            # draw the face detected
            cv2.rectangle(frame, (x_, y_), (x_+w, y_+h), (255, 0, 0), 2)
        (x_, y_, w, h) = faces[0]
        roi = frame[y_:y_+h, x_:x_+w]
        return frame, roi, True