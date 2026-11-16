"""Recreate the original two-note celebration chime, without sampled recordings."""
from pathlib import Path
import math
import struct
import subprocess
import tempfile
import wave

target = Path(__file__).resolve().parents[1] / 'chess_for_anki' / 'web' / 'brilliant.mp3'
rate = 44100
notes = [(0.0, 783.9909, 0.30), (0.13, 1174.6591, 0.27), (0.28, 1567.9817, 0.12)]
with tempfile.TemporaryDirectory() as temporary:
    wav = Path(temporary) / 'chime.wav'
    samples=[]
    for index in range(int(rate*1.05)):
        t=index/rate
        value=0.0
        for onset,frequency,volume in notes:
            age=t-onset
            if age>=0:
                envelope=min(1.0,age/0.009)*math.exp(-age*6.5)
                value+=volume*envelope*(math.sin(2*math.pi*frequency*age)+0.2*math.sin(2*math.pi*frequency*2.01*age))
        samples.append(struct.pack('<h',int(max(-1,min(1,value))*28000)))
    with wave.open(str(wav),'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(b''.join(samples))
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(wav),'-codec:a','libmp3lame','-b:a','96k',str(target)],check=True)
print(target)
