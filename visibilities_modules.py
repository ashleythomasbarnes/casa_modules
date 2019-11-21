from taks import concat

def maketpvisibilities(tpimage,pointings,outputfile='tpvis.ms',lower=0,upper=-1):
    """
    Creates tp visibilities using tp2vis
    """
    rms=image_analysis.computerms(tpimage,lower=lower,upper=upper)
    tp2vis(tpimage, outputfile, pointings, rms=rms)


def concatvis(vislist, outputfile='combinedvis.ms',
              copypointing=False, timesort=True):
    """
    Preferred concat
    """
    concat(vis=vislist, concatvis=outputfile,
           copypointing=copypointing, timesort=timesort)
