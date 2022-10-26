# zr10_sdk
Python implementation of ZR10 SDK by SIYI

* Camera webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
* Documentation: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/download/

# Installation
* Clone this package
    ```bash
    git clone https://github.com/mzahana/zr10_sdk.git
    ```
* Install the CRC16 package
    ```bash
    cd zr10_sdk/crc16-0.1.1/
    python setup.py build
    sudo python setup.py install
    ```
* Done. 
# Usage
* You can go back to the `zr10_sdk` directory and run the `test_*.py` scripts to learn how to use the sdk implementation

* To import this module in your code, copy the `zr10_python.py` script in your code directory, and import as follows, and then follow the test examples
    ```python
    from zr10_python import ZR10SDK
    ```
