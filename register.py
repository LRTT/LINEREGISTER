"""

    Line Auto Register By Phone Number

    * Note !
    If you register too frequent Line will block you

    * How It Work ?
    You will send request data to our server
    Server will generate request body
    Then you will post request body to Line Server
    And Then you will send Line Server Response
    To parse to json data

    - LRT TEAM

"""

from e2ee import E2EE
import base64
import requests
import uuid


class RegisterConfig:
    UA = "Line/10.4.2"
    LA = "ANDROID 10.4.2"
    LAL = "en_us"

    UDID = uuid.uuid4().hex
    DeviceModel = "Nokia 6.1"


class ServerConfig:
    SERVER_URL = "https://lrtt.icu/registerPrimary.do"
    LINE_HOST = "https://ga2s.line.naver.jp/acct/pais/v1"


class LineRegister:
    def __init__(self, phoneNumber, countryCode):
        self.deviceInfo = {
            "udid": RegisterConfig.UDID,
            "deviceModel": RegisterConfig.DeviceModel,
        }

        self.phoneInfo = {
            "phoneNumber": phoneNumber,
            "countryCode": countryCode,
        }

        self.headers = {
            "User-Agent": RegisterConfig.UA,
            "X-Line-Application": RegisterConfig.LA,
            "X-lal": RegisterConfig.LAL
        }

    def postRequest(self, data):
        # here you can modify to use proxy to register !
        return requests.post(ServerConfig.LINE_HOST, data=data, headers=self.headers).content

    def generateRequestData(self, method, data={}):
        return requests.post(ServerConfig.SERVER_URL + "/generate", json={**{"method": method}, **data}).content

    def parseResponseData(self, method, data):
        response = requests.post(ServerConfig.SERVER_URL + "/parse?method=%s" % (method), data=data).json()
        if response["status"] == 200:
            return response
        if "error" in response:
            raise Exception(response["error"])
        raise Exception(response)

    def openSession(self):
        return self.parseResponseData("openSession", self.postRequest(self.generateRequestData("openSession")))

    def getPhoneVerifMethod(self, authSessionId):
        return self.parseResponseData("getPhoneVerifMethod", self.postRequest(self.generateRequestData("getPhoneVerifMethod", {"authSessionId": authSessionId, "deviceInfo": self.deviceInfo, "phoneInfo": self.phoneInfo})))

    def sendPinCodeForPhone(self, authSessionId, verifMethod):
        return self.parseResponseData("sendPinCodeForPhone", self.postRequest(self.generateRequestData("sendPinCodeForPhone", {"authSessionId": authSessionId, "deviceInfo": self.deviceInfo, "phoneInfo": self.phoneInfo, "verifMethod": verifMethod})))

    def verifyPhone(self, authSessionId, pinCode):
        return self.parseResponseData("verifyPhone", self.postRequest(self.generateRequestData("verifyPhone", {"authSessionId": authSessionId, "deviceInfo": self.deviceInfo, "phoneInfo": self.phoneInfo, "pinCode": pinCode})))

    def validateProfile(self, authSessionId):
        return self.parseResponseData("validateProfile", self.postRequest(self.generateRequestData("validateProfile", {"authSessionId": authSessionId})))

    def exchangeEncryptionKey(self, authSessionId, public_key, nonce):
        return self.parseResponseData("exchangeEncryptionKey", self.postRequest(self.generateRequestData("exchangeEncryptionKey", {"authSessionId": authSessionId, "public_key": public_key, "nonce": nonce})))

    def setPassword(self, authSessionId, password, private_key, public_key, nonce, server_public_key, server_nonce):
        return self.parseResponseData("setPassword", self.postRequest(self.generateRequestData("setPassword", {"authSessionId": authSessionId, "password": password, "private_key": private_key, "public_key": public_key, "nonce": nonce, "server_public_key": server_public_key, "server_nonce": server_nonce})))

    def registerPrimaryUsingPhone(self, authSessionId):
        return self.parseResponseData("registerPrimaryUsingPhone", self.postRequest(self.generateRequestData("registerPrimaryUsingPhone", {"authSessionId": authSessionId})))

if __name__ == "__main__":
    password = "YOUR_LINE_PASSWORD"
    
    client = LineRegister("YOUR_PHONE_NUMBER", "YOUR_COUNTRY_CODE")
    
    openSession = client.openSession()
    authSessionId = openSession["authSessionId"]
    
    getPhoneVerifMethod = client.getPhoneVerifMethod(authSessionId)
    if 2 not in getPhoneVerifMethod["availableMethods"]:
        raise Exception("Can't Register With This Phone Number :(")

    sendPinCodeForPhone = client.sendPinCodeForPhone(authSessionId, 2)
    if sendPinCodeForPhone["status"] != 200:
        raise Exception("Fail to sendPinCodeForPhone")
    PIN = input("Pin Code: ")
    
    verifyPhone = client.verifyPhone(authSessionId, PIN)

    validateProfile = client.validateProfile(authSessionId)

    e2ee = E2EE()
    
    private_key = base64.b64encode(e2ee.Curve.private_key).decode()
    public_key = base64.b64encode(e2ee.Curve.public_key).decode()
    nonce = base64.b64encode(e2ee.Curve.nonce).decode()

    exchangeEncryptionKey = client.exchangeEncryptionKey(authSessionId, public_key, nonce)

    setPassword = client.setPassword(authSessionId, password, private_key, public_key, nonce, exchangeEncryptionKey["public_key"], exchangeEncryptionKey["nonce"])
    
    print(client.registerPrimaryUsingPhone(authSessionId))
