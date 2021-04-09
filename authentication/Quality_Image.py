# -*- coding: utf-8 -*-

import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

class Quality_Fingerprint(object):
    def __init__(self, numberFilters = 16, columnsImage = 256, rowsImage = 288, dataFilters = 'data.txt', address_output='./data/', showGraphs = False, name_fingerprint='fingerprint'):
        self.numberFilters = numberFilters
        self.columnsImage = columnsImage
        self.rowsImage =rowsImage
        self.dataFilters = dataFilters
        self.address_output = address_output
        self.showGraphs = showGraphs
        self.name_fingerprint = name_fingerprint

        self._qualityFingerprint = 0 
        self._fileExist = False

        self._optimizeImage = []
        self._dftImage = []
        self.magnitude = []
        self._powerImage = []
        self._R = []
        self._normalizeEnergy = []

    def __optimizeDFT(self, img):
        self.rowsImage= cv.getOptimalDFTSize(self.rowsImage)
        self.columnsImage = cv.getOptimalDFTSize(self.columnsImage)
        self._optimizeImage = np.zeros((self.rowsImage, self.columnsImage))
        self._optimizeImage[:self.rowsImage,:self.columnsImage] = img

    def __DFT2D(self):
        dft = cv.dft(np.float32(self._optimizeImage),flags = cv.DFT_COMPLEX_OUTPUT)
        self._dftImage = np.fft.fftshift(dft)

    def __powerSpectrum(self):
        self.magnitude = cv.magnitude(self._dftImage[:,:,0],self._dftImage[:,:,1])
        self._powerImage = self.magnitude ** 2

    def __bankButterworkFilter(self):
        t = [i for i in range(self.numberFilters)]

        cutOffFrequency = np.zeros((1, self.numberFilters))
        for i in range(self.numberFilters):
            cutOffFrequency[0][i] = (6 + ( 6 * t[i]))

        H = np.zeros((self.numberFilters, self.rowsImage, self.columnsImage))
        for nf in range(self.numberFilters):
            for k in range(self.rowsImage):
                for l in range(self.columnsImage):
                    distance = np.sqrt(np.power(k - (self.rowsImage / 2),2) + np.power(l - (self.columnsImage / 2),2))
                    if distance <= cutOffFrequency[0][nf]:
                        H[nf][k][l] = 1
                    else:
                        H[nf][k][l] = 0

        self._R = np.zeros(((self.numberFilters-1), self.rowsImage, self.columnsImage))
        for i in range((self.numberFilters-1)):
            self._R[i][:][:] = (H[(i+1)][:][:] - H[i][:][:])

    def __loadFilters(self):
        try:
            file = open((self.address_output + self.dataFilters), 'r')
            self._fileExist = True
        except:
            self._fileExist = False

        if self._fileExist:
            self.__obtainBankFilters(file)
            file.close()
            self._fileExist = False
        else:
            self.__bankButterworkFilter()
            self.__saveBankFilters()

    def __saveBankFilters(self):
        with open((self.address_output + self.dataFilters), 'w') as f:
            for nf in range(self.numberFilters - 1):
                for r in range(self.rowsImage):
                    for c in range(self.columnsImage):
                        if (c == self.columnsImage - 1):
                            f.write(str(int(self._R[nf][r][c])) + '\n')
                        else:
                            f.write(str(int(self._R[nf][r][c])) + ',')
                    if (r == self.rowsImage- 1):
                        f.write('#\n')

    def __obtainBankFilters(self, file):
        self._R = np.zeros(((self.numberFilters-1), self.rowsImage, self.columnsImage))
        nf = 0
        m = 0
        n = 0
        while True:
            character = file.read(1)
            if nf >= (self.numberFilters-1):
                break

            if character == '#':
                nf += 1
                m = (-1)
            elif character == '\n':
                m += 1
                n = 0
            elif (character == ',') or (character == ''):
                continue
            else:
                self._R[nf][m][n] = (int(character))
                n += 1

    def __getEnergyImage(self):
        E = np.zeros((self.numberFilters - 1))
        
        for i in range(self.numberFilters - 1):
            E[i] = np.sum( self._powerImage * self._R[i][:][:])

        totalEnergy = np.sum(E)

        self._normalizeEnergy = np.zeros((self.numberFilters))
        self._normalizeEnergy = E / totalEnergy

    def __qualityImage(self):
        T = self._normalizeEnergy.shape

        entropyFingerprint = 0
        for i in range(T[0]):
            if (self._normalizeEnergy[i] != 0):
                entropyFingerprint += (self._normalizeEnergy[i] * np.log(self._normalizeEnergy[i]))
            else:
                continue
            
        entropyFingerprint *= (-1)
        self._qualityFingerprint = np.log(T[0]) - entropyFingerprint

    def __printEntropyImage(self, img, save_plot):
        fig = plt.figure()
        ax1 = fig.add_subplot(221)
        ax1.imshow(img, cmap='gray')
        ax1.set_title('Fingerprint')

        ax2 = fig.add_subplot(222)
        ax2.imshow((20 * np.log(self.magnitude)), cmap='jet')
        ax2.set_title('Power of image')

        ax3 = fig.add_subplot(212)
        ax3.plot(self._normalizeEnergy)
        ax3.set_title('Energy per Filter')
        ax3.set_xlabel('Filters')
        ax3.set_ylabel('Energy')
        
        plt.show()

        if(save_plot):
            fig.savefig(self.address_output + 'Quality_' + self.name_fingerprint + '.png', bbox_inches='tight', dpi=125)

    def getQualityFingerprint(self, img, save_graphs = False):
        img = np.asarray(img)
        self.__optimizeDFT(img)
        self.__loadFilters()
        self.__DFT2D()
        self.__powerSpectrum()
        self.__getEnergyImage()
        self.__qualityImage()
        if (self.showGraphs):
            self.__printEntropyImage(img, save_graphs)
        
        return self._qualityFingerprint

if __name__ == '__main__': 

    img = cv.imread('./authentication/Huella72.bmp',0)
    qualityFingerprint = Quality_Fingerprint(numberFilters = 16, columnsImage = 256, rowsImage = 288, dataFilters = 'dataFilter.txt', showGraphs = True, address_output='./authentication/data/')
    qualityIndex = qualityFingerprint.getQualityFingerprint(img, save_graphs = True)
    print(qualityIndex)


    


    
    

    

    



    
        

