from fontTools.varLib.instancer import *
from fontTools.ttLib import newTable
import sys

def run(infile, outfile, wt):
    ttft=TTFont(infile)
    insname=dict()
    for ins in ttft['fvar'].instances:
        name=ttft['name'].getDebugName(ins.subfamilyNameID)
        if 'wght' not in ins.coordinates: continue
        wght=ins.coordinates['wght']
        insname[name]=wght
    ttft.close()
    
    args=['--no-recalc-timestamp', 
    '--remove-overlaps', 
    #'--update-name-table', 
    '-o', outfile, 
    infile, 
    f'wght={insname[wt]}']
    
    """Partially instantiate a variable font"""
    infile_notuse, axisLimits, options = parseArgs(args)
    
    log.info("Restricting axes: %s", axisLimits)

    log.info("Loading variable font")
    varfont = TTFont(
        infile,
        recalcTimestamp=options.recalc_timestamp,
        recalcBBoxes=options.recalc_bounds,
    )

    isFullInstance = {
        axisTag for axisTag, limit in axisLimits.items() if not isinstance(limit, tuple)
    }.issuperset(axis.axisTag for axis in varfont["fvar"].axes)

    varfont = instantiateVariableFont(
        varfont,
        axisLimits,
        inplace=True,
        optimize=options.optimize,
        overlap=options.overlap,
        updateFontNames=options.update_name_table,
        downgradeCFF2=options.downgrade_cff2,
    )

    suffix = "-instance" if isFullInstance else "-partial"

    log.info("Updating name table")
    varfont['name']=fixname(varfont['name'], wt)
    if wt in ['Regular', 'Bold']:setrbbb(varfont, wt.lower())
    else:setrbbb(varfont, 'other')
    del varfont['STAT']

    log.info(
        "Saving %s font %s",
        "instance" if isFullInstance else "partial variable",
        outfile,
    )
    varfont["head"].yMax = varfont["hhea"].ascender
    varfont["head"].yMin = varfont["hhea"].descender
    varfont.save(outfile)

def setrbbb(font, stylename):
    assert stylename in {"regular", "bold", "italic", "bold italic", 'other'}
    if stylename == "bold":
        font["head"].macStyle = 0b01
    elif stylename == "bold italic":
        font["head"].macStyle = 0b11
    elif stylename == "italic":
        font["head"].macStyle = 0b10
    else:
        font["head"].macStyle = 0b00
    selection = font["OS/2"].fsSelection
    # First clear...
    selection &= ~(1 << 0)
    selection &= ~(1 << 5)
    selection &= ~(1 << 6)
    # ...then re-set the bits.
    if stylename == "regular":
        selection |= 1 << 6
    elif stylename == "bold":
        selection |= 1 << 5
    elif stylename == "italic":
        selection |= 1 << 0
    elif stylename == "bold italic":
        selection |= 1 << 0
        selection |= 1 << 5
    font["OS/2"].fsSelection = selection

def fixname(nameobj, wt):
    newnane=newTable('name')
    for n1 in nameobj.names:
        if n1.nameID>128: continue
        nstr=str(n1)
        if n1.nameID==2 and wt=='Bold':
            nstr='Bold'
        if n1.nameID in (1, 4, 16):nstr=nstr.replace(' VF', '')
        if n1.nameID in (3, 6):nstr=nstr.replace('VF', '')
        
        if n1.nameID==17 and wt in ['Regular', 'Bold']: continue
        if n1.nameID==1 and wt not in ['Regular', 'Bold']:
            newnane.setName(nstr, 16, n1.platformID, n1.platEncID, n1.langID)
        if n1.nameID==4 or (n1.nameID==1 and wt not in ['Regular', 'Bold']):
            nstr+=' '+wt
        if wt!='ExtraLight':
            if n1.nameID==17:
                nstr=wt
            if n1.nameID in (3, 6):
                nstr=nstr.replace('ExtraLight', wt)
        newnane.setName(nstr, n1.nameID, n1.platformID, n1.platEncID, n1.langID)
    return newnane

if __name__=="__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])

