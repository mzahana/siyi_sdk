# siyi_sdk
Python implementation of SIYI SDK for communication with ZR10 and A8 Mini cameras

* Camera webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
* Documentation: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/download/

**If you find this code useful, kindly give a STAR to this repository. Thanks!**
# Installation
* Clone this package
    ```bash
    git clone https://github.com/mzahana/zr10_sdk.git
    ```
* Done. 
# Usage
* You can go back to the `siyi_sdk/tests` directory and run the `test_*.py` scripts to learn how to use the sdk implementation

* To import this module in your code, copy the `siyi_sdk.py` script in your code directory, and import as follows, and then follow the test examples
    ```python
    from siyi_sdk import SIYISDK
    ```
* Example: To run the `test_gimbal_rotation.py` run,
    ```bash
    cd siyi_sdk/tests
    python3 test_gimbal_rotation.py
    ```
