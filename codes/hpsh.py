from fontTools.ttLib import TTFont, newTable

def setcg(cmap, code, glyf):
	for table in cmap.tables:
		if (table.format==4 and code<=0xFFFF) or table.format==12 or code in table.cmap:
			table.cmap[code]=glyf

def mkname(cfg, oldname, locn, ithw='', isvf=False):
	fpsn=oldname.getDebugName(6)
	if locn: locn=' '+locn
	if 'Screen' in fpsn: return scstname(oldname)
	else: return nfname(cfg, oldname, locn, ithw, isvf)

def nfname(cfg, oldname, locn, ithw='', isvf=False):
	fpsn=oldname.getDebugName(6)
	wt=oldname.getDebugName(17)
	if not wt: wt=oldname.getDebugName(2)
	isit='Italic' in wt or 'it' in ithw.lower()
	wt=wt.replace('Italic', '').strip()
	if not wt: wt='Regular'
	ishw='HW' in fpsn or 'hw' in ithw.lower()
	itml, itm, hwm=str(), str(), str()
	if ishw: hwm=' HW'
	if isit: itml, itm=' Italic', 'It'
	locadd=locn.strip()
	if locadd=='ST':
		loctc=' 簡轉繁'
		locsc=' 简转繁'
	else:
		loctc=locsc=locadd
	vfn=str()
	if 'VF' in fpsn: vfn=' VF'
	if 'Sans' in fpsn:
		fmlen=cfg['fontName']+' Sans'+hwm+locn+vfn
		fmlsc=cfg['fontNameSC']+'黑体'+locsc+hwm+vfn
		fmltc=cfg['fontNameTC']+'黑體'+loctc+hwm+vfn
		fmlja=cfg['fontNameJP']+'ゴシック'+loctc+hwm+vfn
	elif 'Serif' in fpsn:
		fmlen=cfg['fontName']+' Serif'+hwm+locn+vfn
		fmlsc=cfg['fontNameSC']+'明朝体'+locsc+hwm+vfn
		fmltc=cfg['fontNameTC']+'明朝體'+loctc+hwm+vfn
		fmlja=cfg['fontNameJP']+'明朝'+loctc+hwm+vfn
	elif 'Mono' in fpsn:
		fmlen=cfg['fontName']+' Mono'+hwm+locn+vfn
		fmlsc=cfg['fontNameSC']+'等宽'+locsc+hwm+vfn
		fmltc=cfg['fontNameTC']+'等寬'+loctc+hwm+vfn
		fmlja=cfg['fontNameJP']+'等幅'+loctc+hwm+vfn
	#elif 'Rounded' in fpsn:
	#	fmlen=cfg['fontName']+' Rounded'+hwm+locn+vfn
	#	fmlsc=cfg['fontNameSC']+'圆角'+locsc+hwm+vfn
	#	fmltc=cfg['fontNameTC']+'圓角'+loctc+hwm+vfn
	else: raise
	nameen, namesc, nametc, nameja=fmlen, fmlsc, fmltc, fmlja
	if not isvf and wt not in ('Regular', 'Bold'):
		nameen+=' '+wt
		namesc+=' '+wt
		nametc+=' '+wt
		nameja+=' '+wt
	#if wt=='Bold':
	if wt in ('Regular', 'Bold') and not (isit and wt=='Regular'):
		fullen=nameen+' '+wt+itml
		fullsc=namesc+' '+wt+itml
		fulltc=nametc+' '+wt+itml
		fullja=nameja+' '+wt+itml
	else:
		fullen=nameen+itml
		fullsc=namesc+itml
		fulltc=nametc+itml
		fullja=nameja+itml
	if isit:
		if wt=='Bold': subfml='Bold Italic'
		else: subfml='Italic'
	elif wt=='Bold':
		subfml='Bold'
	else:
		subfml='Regular'
	psName=fmlen.replace(' ', '')+'-'+fpsn.split('-')[-1].replace('It', '')+itm
	uniqID=cfg['fontVersion']+';'+cfg['fontID'].strip()+';'+psName
	
	newnane=newTable('name')
	newnane.setName(cfg['fontCopyright'], 0, 3, 1, 1033)
	newnane.setName(uniqID, 3, 3, 1, 1033)
	newnane.setName('Version '+cfg['fontVersion'], 5, 3, 1, 1033)
	newnane.setName(psName, 6, 3, 1, 1033)
	newnane.setName(cfg['fontDesigner'], 9, 3, 1, 1033)
	newnane.setName(cfg['fontDiscript'], 10, 3, 1, 1033)
	newnane.setName(cfg['fontVURL'], 11, 3, 1, 1033)
	newnane.setName(oldname.getDebugName(13), 13, 3, 1, 1033)
	newnane.setName(oldname.getDebugName(14), 14, 3, 1, 1033)
	
	newnane.setName(nameen, 1, 3, 1, 1033)
	newnane.setName(fullen, 4, 3, 1, 1033)
	if not isvf and not wt in ('Regular', 'Bold'):
		newnane.setName(fmlen, 16, 3, 1, 1033)
	
	for lanid in (1028, 3076, 5124):
		newnane.setName(nametc, 1, 3, 1, lanid)
		newnane.setName(fulltc, 4, 3, 1, lanid)
		if not isvf and not wt in ('Regular', 'Bold'):
			newnane.setName(fmltc, 16, 3, 1, lanid)
	
	for lanid in (2052, 4100):
		newnane.setName(namesc, 1, 3, 1, lanid)
		newnane.setName(fullsc, 4, 3, 1, lanid)
		if not isvf and not wt in ('Regular', 'Bold'):
			newnane.setName(fmlsc, 16, 3, 1, lanid)
	
	newnane.setName(nameja, 1, 3, 1, 1041)
	newnane.setName(fullja, 4, 3, 1, 1041)
	if not isvf and not wt in ('Regular', 'Bold'):
		newnane.setName(fmlja, 16, 3, 1, 1041)
	
	for lanid in (1033, 1028, 3076, 5124, 2052, 4100, 1041):
		newnane.setName(subfml, 2, 3, 1, lanid)
		if wt not in ('Regular', 'Bold'):
			newnane.setName(wt+itml, 17, 3, 1, lanid)

	if isvf:
		oldnm=fpsn.split('-')[0]
		newnm=fmlen.replace(' ', '')
		for n1 in oldname.names:
			if n1.nameID<255: continue
			nstr=str(n1).replace(oldnm, newnm)
			newnane.setName(nstr, n1.nameID, n1.platformID, n1.platEncID, n1.langID)
	
	return newnane

def scstname(oldname):
	newnane=newTable('name')
	for nm in oldname.names:
		nstr=str(nm)
		if 'Serif Screen' in nstr:
			nstr=nstr.replace('Serif Screen', 'Serif ST Screen')
		elif 'Serif-Screen' in nstr:
			nstr=nstr.replace('Serif-Screen', 'SerifST-Screen')
		elif '屏閲' in nstr:
			nstr+=' 簡轉繁'
		elif '屏阅' in nstr:
			nstr+=' 简转繁'
		newnane.setName(nstr, nm.nameID, nm.platformID, nm.platEncID, nm.langID)
	return newnane
