execfile("/data/beegfs/astro-storage/groups/henning/henshaw/Code/distribute/tp2vis.py")

def maketpvisibilities(tpimage,pointings,outputfile='tpvis.ms',lower=0,upper=-1):
    """
    Creates tp visibilities using tp2vis
    """
    import image_analysis
    rms=image_analysis.computerms(tpimage,lower=lower,upper=upper)
    tp2vis(tpimage, outputfile, pointings, rms=rms)


def concatvis(vislist, outputfile='combinedvis.ms',
              copypointing=False, timesort=True):
    """
    Preferred concat
    """
    from tasks import concat
    concat(vis=vislist, concatvis=outputfile,
           copypointing=copypointing, timesort=timesort)
