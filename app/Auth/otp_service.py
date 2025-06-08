from random import randint

OTP_STORE = {}

def send_mock_otp(email):
    otp = str(randint(100000, 999999))
    OTP_STORE[email] = otp
    print(f"Mock OTP for {email} is {otp}")
    return otp

def verify_mock_otp(email, otp):
    return OTP_STORE.get(email) == otp