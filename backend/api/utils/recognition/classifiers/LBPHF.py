import os
import cv2
import pickle

from PIL import Image
import numpy as np

from api.utils.recognition.Classifier import Classifier

class LBPHF(Classifier):
    def __init__(self):
        super().__init__()
        self.name = "LBPHF"
        self.recognizer = cv2.face.LBPHFaceRecognizer_create(
                            radius = 1, # The radius used for building the Circular Local Binary Pattern. The greater the radius, the smoother the image but more spatial information you can get
                            neighbors = 8, # The number of sample points to build a Circular Local Binary Pattern. An appropriate value is to use 8 sample points. Keep in mind: the more sample points you include, the higher the computational cost
                            grid_x = 8, # The number of cells in the horizontal direction, 8 is a common value used in publications. The more cells, the finer the grid, the higher the dimensionality of the resulting feature vector
                            grid_y = 8, # The number of cells in the vertical direction, 8 is a common value used in publications. The more cells, the finer the grid, the higher the dimensionality of the resulting feature vector
                        )         
        self.labels_file_name = "face_labels_lbphf.pickle"
        self.model_file_name = "lbphf_model.yml"
        self.labels = self.load_labels()
        self.scaleFactor = 1.1 # Parameter specifying how much the image size is reduced at each image scale. It is used to create the scale pyramid.
        self.minNeighbors = 3 # Parameter specifying how many neighbors each candidate rectangle should have, to retain it. A higher number gives lower false positives. 
        self.minSize = (30, 30) # Minimum rectangle size to be considered a face.

    def load_labels(self):
        labels_path = os.path.join(self.labels_root, self.labels_file_name)
        if not os.path.exists(labels_path): 
            return {}
        with open(labels_path, "rb") as f:
            og_labels = pickle.load(f) 
            labels = {v:k for k,v in og_labels.items()} # Inverting key with value
        return labels

    def load_recognizer(self):
        recognizer_path = os.path.join(self.models_root, self.model_file_name)
        if os.path.exists(recognizer_path):
            self.recognizer.read(recognizer_path)  
    
    def train(self):
        current_id = 0
        label_ids = self.load_labels()
        y_lables = [] # Number related to labels
        x_train = [] # Numbers of the pixel values

        print("Inizio training...")

        # For each file in the image directory
        for root, dirs, files in os.walk(self.image_dir):
            for file in files:
                path = os.path.join(root, file) # Save the path of each image
                label = os.path.basename(os.path.dirname(path)).replace(" ", "-").lower() # Save the label of each image
                
                # Assign id to labels
                if not label in label_ids:
                    label_ids[label] = current_id
                    current_id += 1
                id_ = label_ids[label]

                # Turn image into grayscale
                image = Image.open(path).convert("L")

                # Turn the image into a numpy array
                image_array = np.array(image, "uint8") 

                x_train.append(image_array)
                y_lables.append(id_)

                # Face recognition
                faces = self.face_cascade.detectMultiScale(
                    image_array, # Input grayscale image.
                    scaleFactor = self.scaleFactor,
                    minNeighbors = self.minNeighbors, 
                    minSize = self.minSize 
                )

                # Append the detected faces into x_train and their id into y_labels
                for (x, y, w, h) in faces:
                    roi = image_array[y:y+h, x:x+w]
                    x_train.append(roi)
                    y_lables.append(id_)

        # Save labels into file
        label_path = os.path.join(self.labels_root, self.labels_file_name)
        with open(label_path, "wb") as f:
            pickle.dump(label_ids, f)

        # Train items
        train_path = os.path.join(self.models_root, self.model_file_name)
        if os.path.exists(train_path):
            self.recognizer.read(train_path)
        self.recognizer.update(x_train, np.array(y_lables))
        self.recognizer.save(train_path)

        print("Fine training")

    def recognize(self, frame):
        # Turn captured frame into gray scale
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Face recognition
        faces = self.face_cascade.detectMultiScale(
                    gray, # Input grayscale image.
                    scaleFactor = self.scaleFactor,
                    minNeighbors = self.minNeighbors, 
                    minSize = self.minSize 
                )
        if len(faces) == 0:
            name = None
        else:
            name = "unknown"
        conf = 1
        # For each face...
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w] # ...pick its Region of Intrest (from eyes to mouth)

            # Use deep learned model to identify the person
            id_, conf = self.recognizer.predict(roi_gray)
            conf /= 100.
            print(conf)

            # If confidence is good...
            if conf >= .70:
                # ... write who he think he recognized
                name = self.labels[id_]
                super().draw_label(frame, name, x, y)
            # Draw a rectangle around the face
            color = (255, 0, 0) #BGR 0-255 
            stroke = 2
            end_cord_x = x + w
            end_cord_y = y + h
            cv2.rectangle(frame, (x, y), (end_cord_x, end_cord_y), color, stroke)
                        
        return frame, name, conf

######################################
from pathlib import Path
import matplotlib.pyplot as plt

if __name__ == "__main__":

    # TODO 1: retrieve histograms (https://sefiks.com/2020/07/14/a-beginners-guide-to-face-recognition-with-opencv-in-python/)

    # def displayHistogram(target_file):
    #     img = detect_face(target_file)
    #     tmp_model = cv2.face.LBPHFaceRecognizer_create()
    #     tmp_model.train([img], np.array([0]))

    #     histogram = tmp_model.getHistograms()[0][0]
    #     #histogram = histogram[0:100]
    #     axis_values = np.array([i for i in range(0, len(histogram))])

    #     plt.bar(axis_values, histogram)
    #     plt.show()

    def evaluation(image_dir):   
        # Trained model object stores histograms of the images in the facial database. It will compare the histogram of the target image with them later.
        histograms = classifier.recognizer.getHistograms()
        distance_matrix = np.zeros((len(histograms), len(histograms)))
        target_count = 0
        template_count = 0

        # For each file in the image directory
        for root, dirs, files in os.walk(image_dir):
            for target in files:
                # target_img = os.path.join(root, target)
                target_histogram = histograms[target_count][0]
                                
                # target_values = np.array([i for i in range(0, len(target_histogram))])
                
                for template_count in range(0, len(files)):
                     # template_img = os.path.join(root, template)
                    template_histogram = histograms[template_count][0]

                    # template_values = np.array([i for i in range(0, len(template_histogram))])

                    distance_matrix[target_count][template_count] = np.minimum(target_histogram, template_histogram).sum()

                    template_count += 1

                target_count += 1

        np.savetxt('text.txt',distance_matrix,fmt='%.2f')

                #for i in range(0, len(files)):

                # axis_values = np.array([i for i in range(0, len(histogram))])
                # fig = plt.figure(figsize=(10, 5))
                
                # ax1 = fig.add_subplot(1,2,1)
                # plt.imshow(cv2.imread(path)[:,:,::-1])
                # plt.axis('off')
                
                # ax2 = fig.add_subplot(1,2,2)
                # plt.bar(axis_values, histogram)
                # plt.show()

                # fig.savefig(image_dir + "/" + file + "_" + str(count) + ".png")

                # count += 1

        # TODO 2: retrieve distance vector
        # self.collector = cv2.face.StandardCollector_create()
        # self.recognizer.predict_collect(roi_gray, self.collector)
        # list_of_conf_id_tuples = self.collector.getResults()
        # conf = self.collector.getMinDist()
        # id_ = self.collector.getMinLabel()

    classifier = LBPHF()
    classifier.load_recognizer()
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
    image_dir = os.path.join(BASE_DIR, 'samples')

    evaluation(image_dir)