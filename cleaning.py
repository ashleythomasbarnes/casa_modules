### Note that as for Nov. 2019 this code is completely untested and may not function with the newest version of casa
### Use at own risk!

def run_makedirtycube(vis, imagename, imsize, pixelsize,
                      phasecenter='', restfreq='', specmode = 'cube',
                      nchan=-1, width='', start=0,
                      datacolumn='data', outframe='LSRK', gridder='mosaic',
                      deconvolver='multiscale', scales=[0,7,21,63],
                      parallel=False):

    """
    Creates a dirty cube

    Parameters
    ----------
    vis : casa ms visibility file
        input visibilities
    imagename : string w/o extension
        output file name for the dirty cube. Will be appended with _dirty
    imsize : array
        array or x,y list for the size of the output image
    pixelsize : number
        size of the pixels. Hard coded for arcseconds

    remaining parameters are those sent to tclean

    """
    import os
    import masking
    import numpy as np
    from tasks import tclean, imhead, imstat

    #Makes dirty image
    dirtyimage = '%s_dirty' %imagename
    print '[INFO] Making dirty image: %s' %dirtyimage

    tclean(vis            = vis,
           datacolumn     = datacolumn,
           imagename      = dirtyimage,
           imsize         = imsize,
           cell           = str(pixelsize)+'arcsec',
           phasecenter    = phasecenter,
           specmode       = specmode,
           nchan          = nchan,
           start          = start,
           width          = width,
           outframe       = outframe,
           restfreq       = restfreq,
           gridder        = gridder,
           deconvolver    = deconvolver,
           scales         = scales,
           niter          = 0,
           interactive    = False,
           parallel       = parallel)

    #Cleaning up the dir
    #print '[INFO] Cleaning output dir.'
    #os.system('rm -rf %s.weight' %dirtyimage)
    #os.system('rm -rf %s.model' %dirtyimage)
    #os.system('rm -rf %s.psf' %dirtyimage)
    #os.system('rm -rf %s.sumwt' %dirtyimage)

def run_makecleancube(vis, imagename, imsize, pixelsize,
                      phasecenter='', restfreq='', specmode = 'cube',
                      nchan=-1, width='', start=0,
                      datacolumn='data', outframe='LSRK', gridder='mosaic',
                      deconvolver='multiscale', scales=[0,7,21,63],
                      niter=1000000, tp_model = '',usetpmodel=False,
                      n_cycles=5, nsigma_max = 10, nsigma_min=1,
                      parallel=False):

    """
    Code for staggered non-interactive CLEANing in casa.

    This code employs an automasking technique to identify data above a given
    threshold. CLEANing commences and stops when this threshold is hit. In
    the next iteration the previous CLEAN is used as a model for the next cycle.

    The number of steps in the CLEANing process can be finetuned to avoid
    divergence.

    Note that this code requires a dirty cube to be located in the same
    directory as "imagename". This can be produced using run_makedirtycube.

    Parameters
    ----------
    vis : casa ms visibility file
        input visibilities
    imagename : string w/o extension
        output file name for the dirty cube. Will be appended with _dirty
    imsize : array
        array or x,y list for the size of the output image
    pixelsize : number
        size of the pixels. Hard coded for arcseconds
    tp_model : CASA image
        single dish model to use for the CLEANing. Must already be tweaked into
        a useable format
    usetpmodel : bool
        Do you want to use this as a model for the CLEANing? default=no
    n_cycles : number
        number of cycles for the CLEANing
    nsigma_max : number
        starting threshold for mask creation. Given as an integer multiple of
        the rms
    nsigma_min : number
        end threshold for mask creation. i.e. CLEAN down to nsigma_min * rms

    remaining parameters are those sent to tclean

    """
    import os
    import masking
    import numpy as np
    from tasks import tclean, imhead, imstat

    # define thresholds, from 10 to 1
    threshs = np.linspace(nsigma_max, nsigma_min, n_cycles)

    dirtyimage = '%s_dirty' %imagename

    #Makes mask and cleans
    for cycle in range(n_cycles):

        print ''
        previmage = '%s_cycle%i' %(imagename, cycle-1)
        outimage = '%s_cycle%i' %(imagename, cycle)
        print '[INFO] Cleaning cycle %i' %cycle
        print '[INFO] Making image: %s' %outimage
        print ''

        header = imhead(imagename=dirtyimage + '.image', mode='list')
        major = header['perplanebeams']['median area beam']['major']['value']
        minor = header['perplanebeams']['median area beam']['minor']['value']
        beam_area = major*minor
        pixel_area = pixelsize**2
        beam_pixel_ratio = beam_area/pixel_area

        thresh = threshs[cycle]

        print ''
        print '[INFO] Cycle thresh: %0.2f rms' %thresh
        print ''

        if cycle == 0:

            dirtyimage_ = '%s.image' %dirtyimage
            stats = imstat(imagename = dirtyimage_ )
            mad = stats['medabsdevmed'][0]
            print ''
            print '[INFO] Cycle rms: %g Jy/beam' %mad
            print ''

            mask = masking.make_mask_3d(imagename = dirtyimage,
                                        thresh = thresh*mad,
                                        fl = False,
                                        useimage = True,
                                        pixelmin = beam_pixel_ratio*3,
                                        major = major,
                                        minor = minor,
                                        pixelsize = pixelsize,
                                        line = True,
                                        overwrite_old = False)

            startmodel =  ''
            print '[INFO] No model - okay?'

        else:
            print ''
            previmage_ = '%s.image' %previmage
            stats = imstat(imagename=previmage_)
            mad = stats['medabsdevmed'][0]
            print ''
            print '[INFO] Cycle rms: %g Jy/beam' %mad
            print ''

            mask = masking.make_mask_3d(imagename = previmage,
                                        thresh = thresh*mad,
                                        fl = True,
                                        useimage = False,
                                        pixelmin = beam_pixel_ratio*3,
                                        major = major,
                                        minor = minor,
                                        pixelsize = pixelsize,
                                        line = True,
                                        overwrite_old = False)

            startmodel = '%s.model' %previmage
            print ''
            print '[INFO] Using model: %s' %startmodel
            print ''

        tclean(vis            = vis,
               datacolumn     = datacolumn,
               imagename      = outimage,
               imsize         = imsize,
               cell           = str(pixelsize)+'arcsec',
               phasecenter    = phasecenter,
               specmode       = specmode,
               nchan          = nchan,
               start          = start,
               width          = width,
               outframe       = outframe,
               restfreq       = restfreq,
               gridder        = gridder,
               deconvolver    = deconvolver,
               scales         = scales,
               niter          = niter,
               threshold      = thresh*mad,
               interactive    = False,
               mask           = mask,
               startmodel     = startmodel,
               parallel       = parallel)

    #os.system('rm -rf %s.weight' %outimage)
    #os.system('rm -rf %s.model' %outimage)
    #os.system('rm -rf %s.psf' %outimage)
    #os.system('rm -rf %s.sumwt' %outimage)
    #os.system('rm -rf %s.threshmask' %previmage)
    #os.system('rm -rf %s.fullmask' %previmage)
    #os.system('rm -rf %s.fullmask.nopb' %previmage)

    return
