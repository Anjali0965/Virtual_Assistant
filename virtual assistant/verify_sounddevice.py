import sounddevice as sd

devs = sd.query_devices()
for i, d in enumerate(devs):
    if d['max_input_channels'] > 0:
        print(i, d['name'], d['max_input_channels'])
print('Default input device:', sd.default.device)
