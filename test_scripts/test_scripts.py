from client_side import PC2RPi_client

print('Connecting to server...')
client = PC2RPi_client(RPi='Pi_1', port=1515)
client.connect_client()
result = client.request('test')
print(f'Test result: {result}')
client.close_client()
print('Done!')
