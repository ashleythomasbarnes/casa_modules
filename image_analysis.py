def computerms(imagename, lower=0, upper=-1):
    """
    Computes the rms over a given range of channels
    """
    return imstat(imagename,axes=[0,1])['rms'][lower:upper].mean()
