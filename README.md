# EEG-system

NB: If you choose to replicate this project, you do so at your own risk. This is a project that electrically interacts with the human body, and as such there are risks involved. I have designed this system to be as safe as I can make it, but you should still proceed with caution.

This personal project came about as a way to merge two of my interests: physiology and electronics. Electrophysiological signals are the measurable electrical signatures associated with physiological processes. Examples include ECG and EMG for heart and muscle activity respectively. 

## The current state of the project:
Features:
* **Up to 8 channels with 24-bit resolution.** The ADS1298 chip is capable of a maximum of sampling all eight channels at 32k samples/second, but the real limitation is the microcontroller. Practically, a single channel can be broadcast over wifi at about 1000 samples/second. Higher rates can be achieved over a wired connection, or if upgrading the microcontroller.
* **Input referred noise < 5 uV peak-to-peak** (demonstrated to be suitable for EEG, including
SSVEP-based brain-computer interfaces). The system includes up to 12x programmable gain.
* **Battery-powered** for portability, to reduce risk of electric shock, and mitigate contamination from AC noise.
* **Custom GUI written** in Python for device control, data capture, visualization, and analysis
* Capabilities include measuring heart (ECG), muscle (EMG) and brain (EEG) signals.

This repository documents a combination of a python GUI, NodeMCU/arduino code and a PCB design to create a system for acquisition of biological signals. At this point, this project repo includes hardware schematics, circuit board layouts (Eagle CAD files) and firmware (C++), as well as user interface GUI (Python 3.6) which can do the following:
* Connect to a WiFi network and start data collection
* Display real-time readings being collected by the hardware, as well as FFT (frequency spectrum) display.
* Record the time-domain data to a CSV file
* Reset the device
* Toggle the 50 Hz notch filter or high-pass filter on or off
* Change the signal source to choose between the electrodes, the internally generated test signal, or internally shorting the inputs
* Select a different sampling rate, input channel or amplifier gain
* Display the maximum frequency of the signal in the current display window

Below is a photo of the EEG-capturing hardware:

![Hardware](https://github.com/MProx/EEG-system/blob/master/EEG%20hardware.PNG "Hardware")


Below is a demo of the system capturing alpha waves over my occipital lobe (red text added):

![Example Gui](https://github.com/MProx/EEG-system/blob/master/EEG%20GUI.png "Example GUI")


## Areas of ongoing development:
* The wifi transmission of data could do with improvement. It currently employs the UDP "send and forget" protocol, which includes no error checking. This was required to achieve throughput, but might result in interruption of signal during periods of poor signal reception. It might be better to move to bluetooth for transmission.
* Ability to zoom the real-time or FFT plots to a resolution of interest (e.g if working with EMG then we want to see 500Hz - 1000Hz, but for EEG, usually 100Hz is plenty)
* Display multiple channels at once

