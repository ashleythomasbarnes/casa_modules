### Note that as for Nov. 2019 this code is completely untested and may not function with the newest version of casa
### Use at own risk!

def run_makedirtycube(vis, imagename, imsize, pixelsize,
                      phasecenter='', restfreq='',
                      nchan=-1, width='', start=0,
                      datacolumn='data', parallel=False,
                      scales=[0,7,21,63]):

    """

    """
    import os
    import masking
    import numpy as np
    from tasks import tclean, imhead, imstat

    #Makes dirty image
    dirtyimage = '%s_dirty' %imagename
    print '[INFO] Making dirty image: %s' %dirtyimage

    tclean(vis            = vis,
           datacolumn     = 'data',
           imagename      = dirtyimage,
           imsize         = imsize,
           cell           = str(pixelsize)+'arcsec',
           phasecenter    = phasecenter,
           specmode       = 'cube',
           nchan          = nchan,
           start          = start,
           width          = width,
           outframe       = 'LSRK',
           restfreq       = restfreq,
           gridder        = 'mosaic',
           deconvolver    = 'multiscale',
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
                      phasecenter='', restfreq='',
                      nchan=-1, width='', start=0,
                      datacolumn='data', parallel=False,
                      n_cycles=5, scales=[0,7,21,63]):

    ''' Code to conduct basic *cube* cleaning of ALMA data in CASA
        Input:
            [Required]
            vis = Input .ms file
            imagename = Output full path imagename, without extension (e.g. without .image)
            imsize = Size of image in pixels
            cell = Size of cell in arcsec
            [optional]
            phasecenter = Phasecenter for imaging; default is nothing, but not sure if will run without
            restfreq = frequency of line to be imaged, default is nothing, but not sure if will run without
            nchan = number of channels to be imaged: default is all,
            width = width of channels to be imaged: default is 1 channel,
            start = start of channels to be imaged: default is channle 0,
            datacolumn = column in .ms to be imaged; default is 'data' column,
            parallel = conduct clean in parallel; default is False,
        Return
            None
                    '''
    import os
    import masking
    import numpy as np
    from tasks import tclean, imhead, imstat

    # define thresholds, from 10 to 1
    threshs = np.linspace(10, 1, 5)

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
               datacolumn     = 'data',
               imagename      = outimage,
               imsize         = imsize,
               cell           = str(pixelsize)+'arcsec',
               phasecenter    = phasecenter,
               specmode       = 'cube',
               nchan          = nchan,
               start          = start,
               width          = width,
               outframe       = 'LSRK',
               restfreq       = restfreq,
               gridder        = 'mosaic',
               deconvolver    = 'multiscale',
               scales         = scales,
               niter          = 1000000,
               threshold      = thresh*mad,
               interactive    = False,
               mask           = mask,
               startmodel     = startmodel,
               parallel       = parallel)

    os.system('rm -rf %s.weight' %outimage)
    os.system('rm -rf %s.model' %outimage)
    os.system('rm -rf %s.psf' %outimage)
    os.system('rm -rf %s.sumwt' %outimage)
    os.system('rm -rf %s.threshmask' %previmage)
    os.system('rm -rf %s.fullmask' %previmage)
    os.system('rm -rf %s.fullmask.nopb' %previmage)

    return
