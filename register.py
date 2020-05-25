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

    - LRTT TEAM

"""

from e2ee import E2EE
import base64
import requests
import uuid

class Config:
    UA = "Line/9.12.0"
    LA = "ANDROID\t9.12.0\tAndroid OS\t10"
    LAL = "en_us"

    UDID = uuid.uuid4().hex
    DeviceModel = "Nokia 6.1 Plus"

    SERVER_URL = "https://api.lrtt.icu/registerPrimary.do"
    LINE_HOST = "https://gxx.line.naver.jp/acct/pais/v1"

class LineRegister:
    def __init__(self, phoneNumber, countryCode):
        self.deviceInfo = {
            "udid": Config.UDID,
            "deviceModel": Config.DeviceModel,
        }

        self.phoneInfo = {
            "phoneNumber": phoneNumber,
            "countryCode": countryCode,
        }

        self.headers = {
            "User-Agent": Config.UA,
            "X-Line-Application": Config.LA,
            "X-lal": Config.LAL
        }
        
    def post(self, raw_data):
        return requests.post(Config.LINE_HOST, data=raw_data, headers=self.headers).content

    def gen(self, method, data):
        return requests.post(Config.SERVER_URL + "/generate", json={**{"method": method}, **data}).content

    def parse(self, method, raw_data):
        response = requests.post(Config.SERVER_URL + "/parse", params={"method": method}, data=raw_data).json()
        if response["status"] == 200:
            return response
        raise Exception(response)
        
METHODS = {
    'openSession': {
        'args': [],
    },
    'getPhoneVerifMethod': {
        'args': [
            'authSessionId'
        ],
        'self': [
            'deviceInfo',
            'phoneInfo'
        ]
    },
    'sendPinCodeForPhone': {
        'args': [
            'authSessionId',
            'verifMethod'
        ],
        'self': [
            'deviceInfo',
            'phoneInfo'
        ]
    },
    'verifyPhone': {
        'args': [
            'authSessionId',
            'pinCode'
        ],
        'self': [
            'deviceInfo',
            'phoneInfo'
        ]
    },
    'validateProfile': {
        'args': [
            'authSessionId'
        ]
    },
    'exchangeEncryptionKey': {
        'args': [
            'authSessionId',
            'public_key',
            'nonce'
        ]
    },
    'setPassword': {
        'args': [
            'authSessionId',
            'password',
            'private_key',
            'public_key',
            'nonce',
            'server_public_key',
            'server_nonce'
        ]
    },
    'registerPrimaryUsingPhone': {
        'args': [
            'authSessionId'
        ]
    }
}
        
for method in METHODS:
    def create_method(method_name, method_data):
        def wrapper(cls, *args, **kwargs):
            data = {}
            if 'args' in method_data:
                for index, arg in enumerate(args):
                    data[method_data['args'][index]] = arg
                for key, value in kwargs.items():
                    assert key not in data or key not in method_data['args'], '%s already set or %s is invaild args' % (key, key)
                    data[key] = value
            if 'self' in method_data:
                for s_arg in method_data['self']:
                    data[s_arg] = getattr(cls, s_arg)
            return cls.parse(method_name, cls.post(cls.gen(method_name, data)))
        return wrapper
    setattr(LineRegister, method, create_method(method, METHODS[method]))

del METHODS

if __name__ == "__main__":
    print("""
    LINE register by LRTT
    """)
    phoneNumber = input("Phone Number: ") # 080xxxxxxx
    countryCode = input("Country Code: ") # TH (example)
    client = LineRegister(phoneNumber, countryCode)

    openSession = client.openSession()
    authSessionId = openSession["authSessionId"]

    getPhoneVerifMethod = client.getPhoneVerifMethod(authSessionId)
    if 2 not in getPhoneVerifMethod["availableMethods"]:
        raise Exception("Can't Register With This Phone Number :(")

    sendPinCodeForPhone = client.sendPinCodeForPhone(authSessionId, 2)
    if sendPinCodeForPhone["status"] != 200:
        raise Exception("Fail to sendPinCodeForPhone")

    while True: # verify pin (phone)
        try:
            PIN = input("Pin Code: ")
            verifyPhone = client.verifyPhone(authSessionId, PIN)
            break
        except Exception as err:
            err = str(err)
            if 'code=45' in err or 'code=2' in err: # (INVALID_PIN_CODE, DB_FAILED)
                print('invaild pin Code')
                continue
            raise err

    validateProfile = client.validateProfile(authSessionId)

    e2ee = E2EE()
    
    private_key = base64.b64encode(e2ee.Curve.private_key).decode()
    public_key = base64.b64encode(e2ee.Curve.public_key).decode()
    nonce = base64.b64encode(e2ee.Curve.nonce).decode()

    exchangeEncryptionKey = client.exchangeEncryptionKey(authSessionId, public_key, nonce)

    while True: # set password
        try:
            password = input('Password: ')
            setPassword = client.setPassword(authSessionId, password, private_key, public_key, nonce, exchangeEncryptionKey["public_key"], exchangeEncryptionKey["nonce"])
            break
        except Exception as err:
            err = str(err) 
            if 'code=1' in err: # (ILLEGAL_ARGUMENT), maybe invaild password format
                print(err.split("alertMessage='")[1].split("',")[0])
                continue
            raise err

    registerResult = client.registerPrimaryUsingPhone(authSessionId)

    print("Auth Key: " + registerResult["authKey"])
    print("Auth Token: " + registerResult["authToken"])
