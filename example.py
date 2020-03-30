from register import LineRegister
from e2ee import E2EE
import base64

old_input = input
input = lambda string: old_input(string).strip()

PASSWORD = "pasunxwinhery1234"
PHONE_NUMBER = input("Phone Number: ") # 80xxxxxxx
COUNTRY_CODE = input("Country Code: ") # TH

client = LineRegister(PHONE_NUMBER, COUNTRY_CODE)
openSession = client.openSession()
authSessionId = openSession["authSessionId"]
getPhoneVerifMethod = client.getPhoneVerifMethod(authSessionId)
if 2 in getPhoneVerifMethod["availableMethods"]:
    client.sendPinCodeForPhone(authSessionId, 2)
    client.verifyPhone(authSessionId, input("Pin Code: "))
    client.validateProfile(authSessionId)
    e2ee = E2EE()
    private_key = base64.b64encode(e2ee.Curve.private_key).decode()
    public_key = base64.b64encode(e2ee.Curve.public_key).decode()
    nonce = base64.b64encode(e2ee.Curve.nonce).decode()
    exchangeEncryptionKey = client.exchangeEncryptionKey(authSessionId, public_key, nonce)
    client.setPassword(authSessionId, PASSWORD, private_key, public_key, nonce, exchangeEncryptionKey["public_key"], exchangeEncryptionKey["nonce"])
    registerResult = client.registerPrimaryUsingPhone(authSessionId)
    print("Your Auth Key: " + registerResult["authKey"])
    print("Your Auth Key: " + registerResult["authToken"])
else:
    print("Fail to Register")