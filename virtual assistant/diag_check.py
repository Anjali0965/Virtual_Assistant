import config
import sys
print('CONFIG:')
print('  ENABLE_WAKE=', getattr(config, 'ENABLE_WAKE', None))
print('  WAKE_LISTEN_DURATION=', getattr(config, 'WAKE_LISTEN_DURATION', None))
print('  RECORD_DURATION=', getattr(config, 'RECORD_DURATION', None))
print('  SAMPLE_RATE=', getattr(config, 'SAMPLE_RATE', None))
print('  SOUNDDEVICE_DEVICE=', getattr(config, 'SOUNDDEVICE_DEVICE', None))
print('  MIN_RMS=', getattr(config, 'MIN_RMS', None))
print('  MAX_RMS=', getattr(config, 'MAX_RMS', None))

try:
    import sounddevice as sd
    print('\nSounddevice available')
    try:
        print('  sd.default.device =', sd.default.device)
    except Exception as e:
        print('  failed to read sd.default.device:', e)
    try:
        devices = sd.query_devices()
        print('  device count =', len(devices))
        for i, d in enumerate(devices[:10]):
            print(f'    {i}:', d.get('name'))
    except Exception as e:
        print('  query_devices failed:', e)
except Exception as e:
    print('\nSounddevice NOT available:', e)

print('\nSpeech module check')
try:
    import speech
    print('  speech.listen exists:', hasattr(speech, 'listen'))
except Exception as e:
    print('  import speech failed:', e)

print('\nDone')
