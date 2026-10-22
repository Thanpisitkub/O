import sys, os, subprocess, numpy as np
from scipy import signal
from PIL import Image
d = sys.argv[1]; out = sys.argv[2]
names = ["charge","shinra_tensei","shockwave","bansho_tenin","chibaku_core","chibaku_debris","chibaku_collapse","defense"]
tiles = []
for n in names:
    raw = subprocess.run(["ffmpeg","-v","error","-i",os.path.join(d,n+".ogg"),"-f","f32le","-ac","1","-ar","44100","-"],capture_output=True,check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    sr = 44100
    peak = float(np.max(np.abs(x))); rms = float(np.sqrt(np.mean(x**2)))
    head = float(np.sqrt(np.mean(x[:220]**2))); tail = float(np.sqrt(np.mean(x[-220:]**2)))
    f, t, S = signal.spectrogram(x, sr, nperseg=1024, noverlap=768)
    cent = (S * f[:,None]).sum(0) / (S.sum(0) + 1e-12)
    k = len(cent)//5
    cs = [int(cent[i*k:(i+1)*k].mean()) for i in range(5)]
    clip = int((np.abs(x) >= 0.999).sum())
    print(f"{n:17s} dur={len(x)/sr:4.2f}s peak={peak:.2f} rms={20*np.log10(rms+1e-9):6.1f}dBFS head_rms={head:.4f} tail_rms={tail:.4f} clipped={clip} centroid(Hz) over time={cs}")
    S = 10*np.log10(S + 1e-12); S = np.clip((S - S.max() + 90)/90, 0, 1)
    img = Image.fromarray((np.flipud(S[:256])*255).astype(np.uint8)).resize((320,160))
    tiles.append(img)
sheet = Image.new("L",(320*4,160*2))
for i,im in enumerate(tiles): sheet.paste(im,((i%4)*320,(i//4)*160))
sheet.save(out); print("spectrogram sheet", out)
