from fontTools.ttLib import TTFont, newTable
from datetime import datetime

def setcg(cmap, code, glyph):
	for table in cmap.tables:
		if (table.format==4 and code<=0xFFFF) or table.format==12 or code in table.cmap:
			table.cmap[code]=glyph

def mkname(cfg, oldname, vk, isvf=False):
	fpsn=oldname.getDebugName(6)
	if 'Screen' in fpsn: return scstname(oldname)
	else: return nfname(cfg, oldname, vk, isvf)

def nfname(cfg, oldname, vk, isvf=False):
	locn=vk[:2].upper()
	oldps=oldname.getDebugName(6)
	wt=oldname.getDebugName(17)
	if not wt: wt=oldname.getDebugName(2)
	isit='Italic' in wt or 'it' in vk.lower()
	wt=wt.replace('Italic', '').strip()
	if not wt: wt='Regular'
	ishw='HW' in oldps or 'hw' in vk.lower()
	if isit: itnm, itps=' Italic', 'It'
	else: itnm=itps=str()
	for psty in ['Sans', 'Serif', 'Mono', 'Round']:
		if psty in oldps:
			style=psty
			break
	else: raise
	nmobj=dict()
	for l in ['EN', 'TC', 'SC', 'JA']:
		if l in cfg:
			ftfml=cfg[l]['Name']+cfg[l][style]
			if locn!='NM':
				vloc=' '+cfg[l]['ST'] if locn=='ST' else locn
				ftfml+=vloc
			if ishw: ftfml+=' HW'
		else:
			ftfml=cfg['Name']+' '+style
			if ishw: ftfml+=' '+'HW'
			if locn!='NM': ftfml+=' '+locn
		if 'VF' in oldps: ftfml+=' VF'
		ftnm=ftfml
		if not isvf and wt not in ('Regular', 'Bold'):
			ftnm+=' '+wt
		ftfull=ftfml+' '+wt+itnm
		nmobj[l]={'fml': ftfml, 'nm': ftnm, 'full': ftfull}
	lansid={'EN':[1033, ], 'TC':[1028, 3076, 5124], 'SC':[2052, 4100], 'JA':[1041, ]}
	enlan=1033
	if isit: subfml='Bold Italic' if wt=='Bold' else 'Italic'
	else: subfml='Bold' if wt=='Bold' else 'Regular'
	fmlnm=nmobj['EN']['fml']
	psname=fmlnm.replace(' ', '')+'-'+oldps.split('-')[-1].replace('It', '')+itps
	uniqID=cfg['Version']+';'+cfg['ID'].strip()+';'+psname
	Copyright=cfg['Copyright'].format(name=cfg['Name'], year=datetime.now().year)
	newnane=newTable('name')
	idmap={0:Copyright, 3:uniqID, 5:'Version '+cfg['Version'], 6:psname,
		9:cfg['Designer'], 10:style+' font', 11:cfg['VURL'],
		13:oldname.getDebugName(13), 14:oldname.getDebugName(14)}
	for i, v in idmap.items():
		newnane.setName(v, i, 3, 1, enlan)
	for l in ['EN', 'TC', 'SC', 'JA']:
		for lanid in lansid[l]:
			newnane.setName(nmobj[l]['nm'], 1, 3, 1, lanid)
			newnane.setName(nmobj[l]['full'], 4, 3, 1, lanid)
			newnane.setName(subfml, 2, 3, 1, lanid)
			if wt not in ('Regular', 'Bold'):
				newnane.setName(wt+itnm, 17, 3, 1, lanid)
				if not isvf:
					newnane.setName(nmobj[l]['fml'], 16, 3, 1, lanid)
	if isvf:
		oldnm=oldps.split('-')[0]
		newnm=fmlnm.replace(' ', '')
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
