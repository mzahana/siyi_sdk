"""
Python Implementation of ZR10 SDK by SIYI
ZR10 webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
Author : Mohamed Abdelkader
Email: mohamedashraf123@gmail.com
Copyright 2022
"""

class ZR10SDK:
    """
    Implementation of ZR10 SDK communication protocol
    """

    def __init__(self, server_ip: str, port: int) -> None:
        """"
        Params
        --
        server_ip [str] IP address of the camera
        port: [int] UDP port of the camera
        """
        self._server_ip = server_ip
        self._port = port

    def connect(self) -> bool:
        """
        Connects to the camera UDP server using self._server_ip and self._port

        Returns
        --
        True: if connection is established with no errors
        False: if connection is not established
        """
        pass
    def disconnect(self) -> None:
        """
        Disconnect UDP socket
        """
        pass

    def sendMsg(self, msg) -> None:
        """
        Sends a message to the camera

        Params
        --
        msg [str] Message to send
        """
        pass

    def decodeMsg(self) -> None:
        """
        Decodes messages that are received on the rcv buffer, and updates the corresponding fields.
        """
        pass
