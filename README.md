# EEG-system

NB: If you choose to replicate this project, you do so at your own risk. This is a project that electrically interacts with the human body, and as such there are risks involved. I have designed this system to be as safe as I can make it, but there is always a risk. Proceed with caution.

This repo documents a combination of a python GUI, NodeMCU/arduino code and a PCB design to create a system for acquisition of biological signals.

At this point, this project repository includes hardware schematics, circuit board layouts (Eagle CAD files) and firmware (C++), as well as user interface GUI (Python 3.6) which can do the following:
* Connect to a WiFi network and start data collection
* Display real-time readings being collected by the hardware, as well as FFT (frequency spectrum) display.
* Reset the device
* Toggle the 50 Hz notch filter or high-pass filter on or off
* Change the signal source to choose between the electrodes, the internally generated test signal, or internally shorting the inputs
* Select a different sampling rate, input channel or amplifier gain
* Display the maximum frequency of the signal in the current display window

Below is a photo of the EEG-capturing hardware:

![Hardware](https://github.com/MProx/EEG-system/blob/master/EEG%20hardware.PNG "Hardware")


Below is a demo of the system capturing alpha waves over my occipital lobe (red text added):

![Example Gui](https://github.com/MProx/EEG-system/blob/master/EEG%20GUI.png "Example GUI")

This is a project in progress - stay tuned. Future updates will include:
* Ability to zoom the FFT plot to a frequency of interest
* Display multiple channels at once
* Improve high-speed data transfer behaviour
