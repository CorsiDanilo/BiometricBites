from deepface import DeepFace
from ..Classifier import Classifier
import cv2
import pandas as pd
from scipy.spatial.distance import cosine
import os
import numpy as np

class DeepFaceClassifier(Classifier):
    def __init__(self) -> None:
        super().__init__()
        self.GALLERY_PATH = os.path.join(self.models_root, "vggface_gallery.npy")
        self.THRESHOLD = 0.8
        self.gallery = self.load_gallery()
        self.model = DeepFace.build_model("VGG-Face") #Otherwise it would build it on every call for every operation, this is more efficient
        self.name = "VGGFACE" #TODO: remove it once the switch from in the consumer.py file is removed

    def load_gallery(self):
        """
        Loads the gallery array from the file system, if exists
        """
        if os.path.exists(self.GALLERY_PATH):
            return np.load(self.GALLERY_PATH, allow_pickle=True)
        return np.array([])

    def build_gallery(self):
        """
        For each image in the samples directory, it builds the feature vector using VGG Face model, and adds it to the gallery
        then the gallery is saved on the file system, replacing an old one if exists.
        """
        gallery = []
        for root, dirs, files in os.walk(self.image_dir):
            for file in files:
                path = os.path.join(root, file) # Save the path of each image
                name = os.path.basename(os.path.dirname(path)).replace(" ", "-").lower() # Save the label of each image
                image = cv2.imread(path)
                #TODO: in this way, each time the whole gallery is converted to feature vectors, and not only the newest photos
                try:
                    feature_vector = DeepFace.represent(image)
                    gallery.append((name, feature_vector))
                except:
                    pass
        self.gallery = np.array(gallery)
        np.save(self.GALLERY_PATH, self.gallery)

    def train(self):
        """
        Trains the model, in this case this means to build the gallery from the enrolling images' feature vectors. 
        """
        self.build_gallery()
        
    def recognize(self, frame: str):
        """
        Given in input a frame, it returns:
        frame - the modified frame, with the rectangle drawn on the face location
        best_label - the best label (None if the face is not present, "unknwon" if the person isn't recognized)
        confidence - the similarity from the best match (None if not recognized or the face isn't present)
        """
        similarities = []
        frame, roi, face_present = self.detect_faces(frame)
        if not face_present: return frame, None, None
        probe_feature_vector = DeepFace.represent(roi, model=self.model, detector_backend='skip')

        for (label, feature_vector) in self.gallery:
            similarity = 1 - cosine(feature_vector, probe_feature_vector)
            similarities.append((label, similarity))
        best_label, best_similarity = max(similarities, key=lambda x: x[1])
        if best_similarity >= self.THRESHOLD:
            return frame, best_label, best_similarity
        return frame, "Unknown", None

if __name__ == "__main__":
    def test_with_cam():
        DELTA_RECOGNIZE = 5
        counter = 0
        cap = cv2.VideoCapture(0)
        while True:
            counter += 1
            success, frame = cap.read()
            if counter % DELTA_RECOGNIZE == 0:
                counter = 0
                print(classifier.recognize(frame))

            cv2.imshow('Webcam',cv2.flip(frame, 1))
            cv2.waitKey(1)

    classifier = DeepFaceClassifier()
    classifier.train()
    test_with_cam()


    