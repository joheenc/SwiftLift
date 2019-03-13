# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client


# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'ACc1f87118ae6a569933aed14eecfba360'
auth_token = 'uWu'
client = Client(account_sid, auth_token)

message = client.messages \
                .create(
                     body="Hello there Gaurav. Look behind you.",
                     from_='++18482299106',
                     to='+17327425033'
                     #+17327425033
                 )

print(message.sid)
