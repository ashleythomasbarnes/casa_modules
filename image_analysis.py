from tasks import imstat

def computerms(imagename, lower=0, upper=-1):
    """
    Computes the rms over a given range of channels
    """
    return imstat(imagename,axes=[0,1])['rms'][lower:upper].mean()

def calc_beam_area_sd(header):
    import numpy as np
    # beam major FWHM
    bmaj = header['beammajor']['value']
    # beam minor FWHM
    bmin = header['beamminor']['value']
    # beam pa
    pa = header['beampa']['value']
    return (np.pi/(4.*np.log(2))) * bmaj * bmin

def calc_beam_area_perplane(header):
    import numpy as np
    # beam major FWHM
    bmaj = header['perplanebeams']['median area beam']['major']['value']
    # beam minor FWHM
    bmin  = header['perplanebeams']['median area beam']['minor']['value']
    return (np.pi/(4.*np.log(2))) * bmaj * bmin

def sdtomodel(tp, dirtycube, convtojypix=True, pbcorr=True):
    """
    prepares a single dish for conversion to a model for imaging. Assumes image
    is already a casa image file. Also requires a dirty cube of the data you
    intend to merge with.
    """

    print ''
    print tp
    print dirtycube
    print ''
    # First convert to jy per pix if not already done so
    if convtojypix:
        jypiximage = imtojypix(tp)
    else:
        jypiximage = tp

    print jypiximage
    print ''
    print ''
    # regrid SD image to same axes as the dirty cube
    jypiximage_regrid = regridsd(jypiximage, dirtycube)

    if pbcorr:
        attenuate(jypiximage_regrid, dirtycube)

def attenuate(jypiximage_regrid, dirtycube):
    """
    Attenuate the tp image using the primary beam response of the 12m+7m mosaic.
    """
    from tasks import immath

    _pbresponse = '%s.pb' %dirtycube
    jypiximage_regrid_pb = '%s.pb' %jypiximage_regrid

    immath(imagename=[jypiximage_regrid+'.image', _pbresponse],
           outfile=jypiximage_regrid_pb+'.image',
           expr='IM0*IM1')

def regridsd(jypiximage, dirtycube):
    """
    regrids sd to axes of dirty cube
    """
    from tasks import imregrid

    _dirtycube = '%s.image' %dirtycube
    _jypiximage = '%s.image' %jypiximage
    jypiximage_regrid = '%s.regrid' %jypiximage

    imregrid(imagename=_jypiximage, template=_dirtycube,
             output=jypiximage_regrid+'.image')
    return jypiximage_regrid

def imtojypix(tp):
    """
    Converts a single dish image either in k or in jy/beam to jy/pix using
    header information
    """
    from tasks import imhead, immath
    import numpy as np

    _tp = '%s.image' %tp

    # First check the units of the SD image
    header = imhead(_tp, mode='list')
    unit = header['bunit']
    restfreq = header['restfreq']
    restfreq_ghz = restfreq/1.e9 # to GHz

    # beam major FWHM
    bmaj = header['beammajor']['value']
    # beam minor FWHM
    bmin = header['beamminor']['value']

    # get pixel size and convert to arcseconds
    pixelsize = np.abs(header['cdelt1']) * (60.*60.*360.)/(2.*np.pi)

    beamarea = calc_beam_area_sd(header)
    pixelarea = pixelsize**2

    pixperbeam = beamarea/pixelarea

    if (unit == 'K') or (unit=='kelvin') or (unit=='k'):
        # convert to jy/beam
        jybeamimage = '%s.jybeam' %tp
        immath(
        imagename=_tp,
        expr='8.18249739e-7*{0:.6f}*{0:.6f}*IM0*{1:.6f}*{2:.6f}'.format(
            restfreq_ghz, bmaj, bmin),
        outfile=jybeamimage+'.image',
        )
        imhead(jybeamimage+'.image', mode='put', hdkey='bunit', hdvalue='Jy/beam')

    else:
        jybeamimage = tp

    jypiximage = '%s.jypix' %tp
    immath(imagename=jybeamimage+'.image',expr='IM0/{0:.6f}'.format(pixperbeam),
           outfile=jypiximage+'.image',)
    imhead(jypiximage+'.image', mode='put', hdkey='bunit', hdvalue='Jy/pixel')
    return jypiximage
