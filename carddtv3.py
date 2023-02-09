
import numpy as np
import argparse
import cv2
import imutils
import re
import time
#import json
'''python3 carddtv3.py -i img/18.jpg'''

# define parameters/cordinates for images 
def order_points(pts):
    rect =	rect = np.zeros((4, 2), dtype = "float32")

    s = pts.sum(axis = 1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect



# load img and find fix cordinate for transformation
def four_point_transform(image, pts):
    rect = order_points(pts)
    (t1, tr, br, b1) = rect

    widthA = np.sqrt(((br[0] - b1[0]) ** 2) + ((br[1] - br[1]) ** 2))
    widthB = np.sqrt(((tr[0] - t1[0]) ** 2) + ((tr[1] - t1[1]) ** 2))
    maxwidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((t1[0] -b1[0] ) ** 2) + ((t1[1] - b1[1]) ** 2))
    maxheight = max(int(heightA), int(heightB))

    dest = np.array([
        [0, 0],
        [maxwidth - 1, 0],
        [maxwidth - 1, maxheight - 1],
        [0, maxheight - 1]], dtype = "float32")



# transform cordinate in matrix form and stored in dest
    Mt = cv2.getPerspectiveTransform(rect, dest)
    warped = cv2.warpPerspective(image, Mt, (maxwidth, maxheight))

    return warped
    #print (warped)

def rotate_bound(image, angle):
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)

    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])

    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))

    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY

    # perform the actual rotation and return the image
    return cv2.warpAffine(image, M, (nW, nH))


def remove_small_objects(img, min_size=700):
        # find all your connected components (white blobs in your image)
        nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(img, connectivity=8)
        # connectedComponentswithStats yields every seperated component with information on each of them, such as size
        # the following part is just taking out the background which is also considered a component, but most of the time we don't want that.
        sizes = stats[1:, -1]
        nb_components = nb_components - 1

        # your answer image
        img2 = img
        # for every component in the image, you keep it only if it's above min_size
        for i in range(0, nb_components):
            if sizes[i] < min_size:
                img2[output == i + 1] = 0

        return img2

def detect_card(image):

    ratio = image.shape[0] / 500.0
    #print(ratio)
    orig = image.copy()
    image = imutils.resize(image, height = 500)
    
    #image into gray
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edged = cv2.Canny(gray, 25, 25)
    
    edged = remove_small_objects(edged)
    
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
    dilated = cv2.dilate(edged, element)
    #dilated = cv2.erode(dilated, element)
    
    cnts = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
    screencnt = None
    #print(cnts)
    
    # loop over the contours
    for c in cnts:
            
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            #print(approx)
    
            if len(approx) == 4:
                    screencnt = approx
                    break
    
    if screencnt is None:
        return None
    
    warped = four_point_transform(orig, screencnt.reshape(4, 2) * ratio )
    h, w = warped.shape[:2]
    if h > w * 1.2:
        M = rotate_bound(warped, -90)
    else:
        M = warped
    
    imS = imutils.resize(M, height = 350)
    #imS = cv2.resize(M, (650, 350))
    
    return imS

if __name__ == "__main__":
    #construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required= True,
        help = "Path to the image to be scanned")
    args =vars(ap.parse_args())

    #edge detection
    image = cv2.imread(args["image"])
    st = time.time()
    imS = detect_card(image)
    print(time.time() - st)
    cv2.imshow("output", imS)
    #cv2.imwrite('out/'+ 'Output Image.PNG', imS)
    cv2.waitKey(0)

