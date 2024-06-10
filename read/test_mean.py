import cv2
import numpy as np

# Load the image
# im = cv2.imread('start.png')
#
# # Calculate mean of green area
# A = np.mean(im[600:640, 20:620], axis=(0,1))


from PIL import Image
i = Image.open("ttt.png")
colors = sorted(i.getcolors())
c_1 = colors[-1]
c_2 = colors[-2]
'#%02x%02x%02x' % colors[-2][1]
pass