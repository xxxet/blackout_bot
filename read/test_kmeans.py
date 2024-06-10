
from cv2 import kmeans, TERM_CRITERIA_MAX_ITER, TERM_CRITERIA_EPS, KMEANS_RANDOM_CENTERS, imread, cvtColor, \
    COLOR_BGR2RGB
from numpy import float32, uint8, unique
from matplotlib.pyplot import show, imshow

# Read image
img = imread('../group5.jpg')

# Convert it from BGR to RGB
img_RGB = cvtColor(img, COLOR_BGR2RGB)

# Reshape image to an Mx3 array
img_data = img_RGB.reshape(-1, 3)

# Find the number of unique RGB values
print(len(unique(img_data, axis=0)), 'unique RGB values out of', img_data.shape[0], 'pixels')

# Specify the algorithm's termination criteria
criteria = (TERM_CRITERIA_MAX_ITER + TERM_CRITERIA_EPS, 10, 1.0)

###############################################

# Run the k-means clustering algorithm on the pixel values
compactness, labels, centers = kmeans(data=img_data.astype(float32), K=5, bestLabels=None, criteria=criteria,
                                      attempts=10, flags=KMEANS_RANDOM_CENTERS)

# Apply the RGB values of the cluster centers to all pixel labels
colours = centers[labels].reshape(-1, 3)

# Find the number of unique RGB values
print(len(unique(colours, axis=0)), 'unique RGB values out of', img_data.shape[0], 'pixels')

# Reshape array to the original image shape
img_colours = colours.reshape(img_RGB.shape)

# Display the quantized image
imshow(img_colours.astype(uint8))
show()