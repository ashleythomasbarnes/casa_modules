def catpointings(listobsfile, outputfile='12m.ptg', sourcename='source', epoch='J2000'):
    """
    Extracts pointing locations for use with tp2vis
    """
    out_file=open(outputfile,"w+")

    with open(listobsfile) as origin_file:
        for line in origin_file:
            if 'none' in line:
                line=line.split(sourcename+' ')[1]
                line=line.split(epoch)[0]
                x=line.split(' ')[0]
                y=line.split(' ')[1]
                out_file.write("%s %s %s\n" % (epoch, x, y))
        out_file.close()
