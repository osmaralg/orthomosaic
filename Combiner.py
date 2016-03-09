import cv2
import numpy as np
import utilities as util
import geometry as gm
import pyramidBlending

class Combiner:
    def __init__(self,imageList_,dataMatrix_):
        self.imageList = []
        self.kpList = []
        self.dataMatrix = dataMatrix_
        detector = cv2.ORB()
        for i in range(0,len(imageList_)):
            image = imageList_[i]
            gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            kp = detector.detect(image,None)
            M = gm.computeUnRotMatrix(self.dataMatrix[i,:])
            correctedImage, correctedKP = gm.warpPerspectiveWithPadding(imageList_[i],M,kp)
            self.imageList.append(correctedImage)
            self.kpList.append(correctedKP)
            test = cv2.drawKeypoints(correctedImage,correctedKP,color=(0,0,255))
            util.display("TEST",test)

    def createMosaic(self):
        for i in range(1,len(self.imageList)):
            image = self.imageList[i]
            M = gm.computeUnRotMatrix(self.dataMatrix[i,:])
            correctedImage = gm.warpWithPadding(image,M)
            combinedResult = self.combine(self.result,correctedImage)
            self.result = combinedResult
        return self.result

    def combine(self, index1, index2):
        '''
        :param index1: index of self.imageList and self.kpList to combine
        :param index2: index of self.imageList and self.kpList to combine
        :return:
        '''
        

        '''Feature detection and matching'''
        detector = cv2.ORB()
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING2, crossCheck=True)
        gray1 = cv2.cvtColor(image1,cv2.COLOR_BGR2GRAY)
        kp1, descriptors1 = detector.detectAndCompute(gray1,None)
        gray2 = cv2.cvtColor(image2,cv2.COLOR_BGR2GRAY)
        kp2, descriptors2 = detector.detectAndCompute(gray2,None)
        matches = matcher.match(descriptors2,descriptors1)
        matchDrawing = util.drawMatches(gray1,kp1,gray2,kp2,matches)
        util.display("matches",matchDrawing)
        cv2.imwrite("matchDrawing.png",matchDrawing)
        src_pts = np.float32([ kp2[m.queryIdx].pt for m in matches ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp1[m.trainIdx].pt for m in matches ]).reshape(-1,1,2)

        '''Compute Affine Transform'''
        A = cv2.estimateRigidTransform(src_pts,dst_pts,fullAffine=False)
        print "A"
        print A

        '''Compute 4 Image Corners Locations'''
        height1,width1 = image1.shape[:2]
        height2,width2 = image2.shape[:2]
        corners1 = np.float32(([0,0],[0,height1],[width1,height1],[width1,0]))
        corners2 = np.float32(([0,0],[0,height2],[width2,height2],[width2,0]))
        warpedCorners2 = np.zeros((4,2))
        for i in range(0,4):
            cornerX = corners2[i,0]
            cornerY = corners2[i,1]
            warpedCorners2[i,0] = A[0,0]*cornerX + A[0,1]*cornerY + A[0,2]
            warpedCorners2[i,1] = A[1,0]*cornerX + A[1,1]*cornerY + A[1,2]
        allCorners = np.concatenate((corners1, warpedCorners2), axis=0)
        [xMin, yMin] = np.int32(allCorners.min(axis=0).ravel() - 0.5)
        [xMax, yMax] = np.int32(allCorners.max(axis=0).ravel() + 0.5)

        '''Compute Image Alignment'''
        translation = np.float32(([1,0,-1*xMin],[0,1,-1*yMin],[0,0,1]))
        warpedImage1 = cv2.warpPerspective(image1, translation, (xMax-xMin, yMax-yMin))
        warpedImageTemp = cv2.warpPerspective(image2, translation, (xMax-xMin, yMax-yMin))
        warpedImage2 = cv2.warpAffine(warpedImageTemp, A, (xMax-xMin, yMax-yMin))
        #returnWarpedImage2 = np.copy(warpedImage2)

        warpedGray1 = cv2.warpPerspective(gray1, translation, (xMax-xMin, yMax-yMin))
        warpedGrayTemp = cv2.warpPerspective(gray2, translation, (xMax-xMin, yMax-yMin))
        warpedGray2 = cv2.warpAffine(warpedGrayTemp, A, (xMax-xMin, yMax-yMin))

        '''Compute Mask for Image Combination'''
        ret, mask1 = cv2.threshold(warpedGray1,1,255,cv2.THRESH_BINARY_INV)
        mask1 = np.float32(mask1)/255

        warpedImage2[:,:,0] = warpedImage2[:,:,0]*mask1
        warpedImage2[:,:,1] = warpedImage2[:,:,1]*mask1
        warpedImage2[:,:,2] = warpedImage2[:,:,2]*mask1

        result = warpedImage1 + warpedImage2
        util.display("result",result)
        return result

