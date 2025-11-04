import av

if __name__ == '__main__':
    print("PyAV OK")
    c = av.open("https://bt-01-pull.g33-video.com/nw35/8-351.flv", timeout=3)
    print("Open OK")
    c.close()
    print("Close OK")
