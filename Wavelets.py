# Experimental script that pulls data from c:\EEG.txt, and removes noise using a 3rd-level wavelet transform 
# and soft-thresholding on the detail coefficients before using the inverse transform. The threshold is set to 
# 15% of the respective maxima for each coefficient array (one at each level).

import matplotlib.pyplot as plt
import pywt

file_object  = open('C:\EEG.txt', 'r')
raw_data = file_object.readlines()

index = []
data = []

for i in range(len(raw_data)-1):
    x, y = raw_data[i].split("\t")
    X = float(x)
    Y = float(y)
    index.append(X)
    data.append(Y)

[cA, cD3, cD2, cD1] = pywt.wavedec(data, 'sym4', level=3)

threshold = 0.15

plt.figure()

plt.subplot(3, 1, 1)
plt.title("Wavelet transform coefficients: cD1")
plt.plot(cD1)
cD1 = pywt.threshold(cD1, threshold*max(cD1))
plt.plot(cD1)

plt.subplot(3, 1, 2)
plt.title("Wavelet transform coefficients: cD2")
plt.plot(cD2)
cD2 = pywt.threshold(cD2, threshold*max(cD2))
plt.plot(cD2)

plt.subplot(3, 1, 3)
plt.title("Wavelet transform coefficients: cD3")
plt.plot(cD3)
cD3 = pywt.threshold(cD3, threshold*max(cD3))
plt.plot(cD3)

plt.tight_layout()
plt.show()

datarec = pywt.waverec([cA, cD3, cD2, cD1], 'sym4')

plt.figure()
plt.subplot(2, 1, 1)
plt.plot(index[:15000], data[:15000])
plt.xlabel('time (s)')
plt.ylabel('microvolts (uV)')
plt.title("Raw signal")
plt.ylim([-130,400])
plt.subplot(2, 1, 2)
plt.plot(index[:15000], datarec[:15000])
plt.xlabel('time (s)')
plt.ylabel('microvolts (uV)')
plt.title("De-noised signal using wavelet techniques")
plt.ylim([-130,400])

plt.tight_layout()
plt.show()
