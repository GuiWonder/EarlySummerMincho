import os, json, sys
from fontTools.ttLib import TTFont, newTable
from hpsh import *

pydir=os.path.abspath(os.path.dirname(__file__))
cfg=json.load(open(os.path.join(pydir, 'configs/config.json'), 'r', encoding='utf-8'))

def glfrtxt(txt):
	cmap=font.getBestCmap()
	glys=list()
	for ch in txt:
		if ord(ch) in cmap and cmap[ord(ch)] not in glys:
			glys.append(cmap[ord(ch)])
	return glys
def glyrepl(repdic):
	for table in font["cmap"].tables:
		for cd in table.cmap:
			if table.cmap[cd] in repdic:
				table.cmap[cd]=repdic[table.cmap[cd]]
				print('Remapping', chr(cd))
def locllki(ftgsub, lan):
	ftl, lkl=list(), list()
	for sr in ftgsub.table.ScriptList.ScriptRecord:
		for lsr in sr.Script.LangSysRecord:
			if lsr.LangSysTag.strip()==lan:
				ftl+=lsr.LangSys.FeatureIndex
	for ki in ftl:
		ftg=ftgsub.table.FeatureList.FeatureRecord[ki].FeatureTag
		if ftg=='locl':
			lkl+=ftgsub.table.FeatureList.FeatureRecord[ki].Feature.LookupListIndex
	return list(dict.fromkeys(lkl))
def getloclk(ckfont, lan):
	locdics=list()
	for lki in locllki(ckfont["GSUB"], lan):
		locrpl=dict()
		for st in ckfont["GSUB"].table.LookupList.Lookup[lki].SubTable:
			if st.LookupType==7 and st.ExtSubTable.LookupType==1:
				tabl=st.ExtSubTable.mapping
			elif st.LookupType==1:
				tabl=st.mapping
			for g1 in tabl:
				locrpl[g1]=tabl[g1]
		locdics.append(locrpl)
	return locdics
def glfrloc(gl, loclk):
	for dc in loclk:
		if gl in dc: return dc[gl]

def locglrpl(newmap):
	locgls=dict()
	shset=json.load(open(os.path.join(pydir, 'configs/sourcehan.json'), 'r', encoding='utf-8'))
	krgl, scgl, tcgl, hcgl=glfrtxt(shset['krgl']), glfrtxt(shset['scgl']), glfrtxt(shset['tcgl']), glfrtxt(shset['hcgl'])
	for glloc in ((krgl, lockor), (scgl, loczhs), (tcgl, loczht), (hcgl, loczhh)):
		for g1 in glloc[0]:
			assert g1 not in locgls, g1
			g2=glfrloc(g1, glloc[1])
			if g2: locgls[g1]=g2
	cmap=font.getBestCmap()
	for cd in cmap:
		if cmap[cd] in locgls:
			assert cd not in newmap, chr(cd)
			newmap[cd]=locgls[cmap[cd]]

def setuvs(newmap, uvdic):
	uvcfg=json.load(open(os.path.join(pydir, 'configs/uvs.json'), 'r', encoding='utf-8'))
	tv=dict()
	for ch in uvcfg.keys():
		tv[ord(ch)]=int(uvcfg[ch], 16)
	for k in uvdic.keys():
		if k in tv and tv[k] in uvdic[k]:
			g=uvdic[k][tv[k]]
			if k in newmap:
				if newmap[k]==g: continue
				else: raise RuntimeError(chr(k), newmap[k], g)
			newmap[k]=g
def glfruv(fontob, ch, uv):
	cmapob=fontob.getBestCmap()
	for table in fontob["cmap"].tables:
		if table.format==14 and uv in table.uvsDict:
			for cg in table.uvsDict[uv]:
				if cg[0]==ord(ch):
					if cg[1]==None: return cmapob[cg[0]]
					else: return cg[1]
	raise RuntimeError(ch)
def ckdlg():
	rplg=dict()
	for ch in '成':
		rplg[glfruv(font, ch, 0xE0100)]=glfruv(font, ch, 0xE0101)
	dllk=set()
	for ki in font["GSUB"].table.FeatureList.FeatureRecord:
		if ki.FeatureTag=='dlig': dllk.update(ki.Feature.LookupListIndex)
	for i in dllk:
		for st in font["GSUB"].table.LookupList.Lookup[i].SubTable:
			if st.LookupType==7: stbl=st.ExtSubTable
			else: stbl=st
			if stbl.LookupType!=4: continue
			for lgg in list(stbl.ligatures):
				for lg in list(stbl.ligatures[lgg]):
					for ilin in range(len(lg.Component)):
						if lg.Component[ilin] in rplg:
							lg.Component[ilin]=rplg[lg.Component[ilin]]
def locvar(newmap):
	cmap=font.getBestCmap()
	jpvch=[('𰰨', '芲'), ('𩑠', '頙'), ('鄉', '鄕'), ('唧', '喞'), ('概', '槪'), ('𥄳', '眔')]
	radic=[('⽉', '月'), ('⻁', '虎'), ('⾳', '音'), ('⿓', '龍'), ('⼾', '戶')]
	for chs in jpvch+radic:
		if ord(chs[1]) in cmap:
			c=ord(chs[0])
			assert c not in newmap, chr(c)
			newmap[c]=cmap[ord(chs[1])]
	locscv=[('𫜹', '彐'), ('𣽽', '潸')]
	for lv1 in locscv:
		if ord(lv1[1]) in cmap:
			c=ord(lv1[0])
			assert c not in newmap, chr(c)
			gv2=glfrloc(cmap[ord(lv1[1])], loczhs)
			if gv2:
				newmap[c]=gv2

def uvsvar(newmap, uvdic):
	uvsmul=[('⺼', '月', 'E0100'), ('𱍐', '示', 'E0100'), ('䶹', '屮', 'E0101'), ('𠾖', '器', 'E0100'), ('𡐨', '壄', 'E0100'), ('𤥨', '琢', 'E0101'), ('𦤀', '臭', 'E0100'), ('𨺓', '隆', 'E0100'), ('𫜸', '叱', 'E0101'), ('廄', '廏', 'E0101'), ('溉', '漑', 'E0102')]
	for uvm in uvsmul:
		u1, u2, usel=ord(uvm[0]), ord(uvm[1]), int(uvm[2], 16)
		if u2 in uvdic and usel in uvdic[u2]:
			assert u1 not in newmap, chr(u1)
			newmap[u1]=uvdic[u2][usel]

def rmlk(font, tbnm, i):
	font[tbnm].table.LookupList.Lookup.pop(i)
	for ki in font[tbnm].table.FeatureList.FeatureRecord:
		newft=list()
		for j in ki.Feature.LookupListIndex:
			if j>i: newft.append(j-1)
			elif j<i: newft.append(j)
		ki.Feature.LookupListIndex=newft
	if tbnm=='GSUB':
		for lkp in font[tbnm].table.LookupList.Lookup:
			for st in lkp.SubTable:
				if st.LookupType in (5, 6) and hasattr(st, 'SubstLookupRecord'):
					for sbrcd in st.SubstLookupRecord:
						if sbrcd.LookupListIndex>i:
							sbrcd.LookupListIndex-=1
def rmft(font, tbnm, i):
	font[tbnm].table.FeatureList.FeatureRecord.pop(i)
	for sr in font[tbnm].table.ScriptList.ScriptRecord:
		newdl=list()
		for j in sr.Script.DefaultLangSys.FeatureIndex:
			if j>i: newdl.append(j-1)
			elif j<i: newdl.append(j)
		sr.Script.DefaultLangSys.FeatureIndex=newdl
		for lsr in sr.Script.LangSysRecord:
			newln=list()
			for j in lsr.LangSys.FeatureIndex:
				if j>i: newln.append(j-1)
				elif j<i: newln.append(j)
			lsr.LangSys.FeatureIndex=newln
def rmopty(fttg):
	loclks, locfts=list(), list()
	for i in range(len(font["GSUB"].table.FeatureList.FeatureRecord)):
		if font["GSUB"].table.FeatureList.FeatureRecord[i].FeatureTag==fttg:
			loclks+=font["GSUB"].table.FeatureList.FeatureRecord[i].Feature.LookupListIndex
			locfts.append(i)
	loclks=list(set(loclks))
	loclks.sort(reverse=True)
	locfts=list(set(locfts))
	locfts.sort(reverse=True)
	for i in locfts: rmft(font, 'GSUB', i)
	for i in loclks: rmlk(font, 'GSUB', i)
def subcff(cfftb, glyphs):
	ftcff=cfftb.cff
	for fontname in ftcff.keys():
		fontsub=ftcff[fontname]
		cs=fontsub.CharStrings
		for g in fontsub.charset:
			if g not in glyphs: continue
			c, _=cs.getItemAndSelector(g)
		if cs.charStringsAreIndexed:
			indices=[i for i,g in enumerate(fontsub.charset) if g in glyphs]
			csi=cs.charStringsIndex
			csi.items=[csi.items[i] for i in indices]
			del csi.file, csi.offsets
			if hasattr(fontsub, "FDSelect"):
				sel=fontsub.FDSelect
				sel.format=None
				sel.gidArray=[sel.gidArray[i] for i in indices]
			newCharStrings={}
			for indicesIdx, charsetIdx in enumerate(indices):
				g=fontsub.charset[charsetIdx]
				if g in cs.charStrings:
					newCharStrings[g]=indicesIdx
			cs.charStrings=newCharStrings
		else:
			cs.charStrings={g:v
					  for g,v in cs.charStrings.items()
					  if g in glyphs}
		fontsub.charset=[g for g in fontsub.charset if g in glyphs]
		fontsub.numGlyphs=len(fontsub.charset)
def cffinf():
	if 'CFF ' in font:
		cff=font['CFF '].cff
		fmln=cfg['fontName']
		for ss in ('Sans', 'Serif', 'Mono'):
			if ss in fpsn: fmln+=' '+ss
		psn=fmln.replace(' ', '')
		pso=cff.fontNames[0].split('-')[0]
		fmlo=cff[0].FamilyName
		cff.fontNames[0]=cff.fontNames[0].replace(pso, psn)
		cff[0].FamilyName=fmln
		cff[0].FullName=cff[0].FullName.replace(fmlo, fmln)
		cff[0].Notice=cfg['fontCopyright']
		cff[0].CIDFontVersion=float(cfg['fontVersion'])
		for dic in cff[0].FDArray:
			dic.FontName=dic.FontName.replace(pso, psn)
	elif 'glyf' in font:
		font["head"].yMax = font["hhea"].ascender
		font["head"].yMin = font["hhea"].descender

def subgl():
	cmap=font.getBestCmap()
	'''Remove hangul'''
	font['cmap'].tables=[table for table in font['cmap'].tables if table.format!=14]
	for table in font["cmap"].tables:
		table.cmap={code:table.cmap[code] for code in table.cmap if code not in range(0xa960, 0xd7ff) and code not in range(0x1100, 0x1200) and code not in range(0x2b8b8, 0x2ce94) and code not in range(0x3200, 0x3300)}
	cmap=font.getBestCmap()
	rmopty('nlck')
	rmopty('jp78')
	rmopty('jp83')
	rmopty('jp90')
	rmopty('calt')
	rmopty('ljmo')
	rmopty('tjmo')
	rmopty('vjmo')
	rmopty('aalt')

	rmlkre=set()
	for li in range(len(font["GSUB"].table.LookupList.Lookup)):
		lkp=font["GSUB"].table.LookupList.Lookup[li]
		for st in lkp.SubTable:
			if st.LookupType in (5, 6) and hasattr(st, 'SubstLookupRecord'):
				rmlkre.add(li)
				break

	usdlk=set()
	for ftr in font["GSUB"].table.FeatureList.FeatureRecord:
		ftr.Feature.LookupListIndex=[idx for idx in ftr.Feature.LookupListIndex if idx not in rmlkre]
		usdlk.update(ftr.Feature.LookupListIndex)

	usdlkex=set()
	rmlkex=list()
	for ilk in range(len(font["GSUB"].table.LookupList.Lookup)):
		if ilk not in usdlk:
			rmlkex.append(ilk)
	rmlkex.sort(reverse=True)
	for i in rmlkex: rmlk(font, 'GSUB', i)

	usedg=set()
	usedg.add('.notdef')
	usedg.update(cmap.values())
	pungl=glfrtxt(pzhs+pzht+simpcn)
	print('Checking Lookup table...')
	loclks=list()
	for i in range(len(font["GSUB"].table.FeatureList.FeatureRecord)):
		if font["GSUB"].table.FeatureList.FeatureRecord[i].FeatureTag=='locl':
			loclks+=font["GSUB"].table.FeatureList.FeatureRecord[i].Feature.LookupListIndex
	for lki in set(loclks):
		for st in font["GSUB"].table.LookupList.Lookup[lki].SubTable:
			if st.LookupType==7: stbl=st.ExtSubTable
			else: stbl=st
			assert stbl.LookupType==1
			tabl=stbl.mapping
			for k1 in list(tabl.keys()):
				if k1 in pungl or tabl[k1] in pungl:
					usedg.add(k1)
					usedg.add(tabl[k1])
				else:
					del tabl[k1]
	for ki in font["GSUB"].table.LookupList.Lookup:
		for st in ki.SubTable:
			if st.LookupType==7: stbl=st.ExtSubTable
			else: stbl=st
			lktp=stbl.LookupType
			if lktp==1:
				tabl=stbl.mapping
				for g1, g2 in list(tabl.items()):
					if g1 in usedg:
						usedg.add(g2)
					else:
						del tabl[g1]
			elif lktp==3:
				for item in list(stbl.alternates.keys()):
					if item in usedg:
						usedg.update(set(stbl.alternates[item]))
					else:
						del stbl.alternates[item]
			elif lktp==4:
				for li in list(stbl.ligatures):
					for lg in list(stbl.ligatures[li]):
						a=list(lg.Component)
						a.append(li)
						if set(a).issubset(usedg):
							usedg.add(lg.LigGlyph)
						else:
							stbl.ligatures[li].remove(lg)
					if len(stbl.ligatures[li])<1:
						del stbl.ligatures[li]
			elif lktp==5:
				if hasattr(stbl, 'Coverage'):
					for tb in stbl.Coverage:
						usedg.update(tb.glyphs)
			elif lktp==6:
				for tb in stbl.BacktrackCoverage:
					usedg.update(tb.glyphs)
				for tb in stbl.InputCoverage:
					usedg.update(tb.glyphs)
				for tb in stbl.LookAheadCoverage:
					usedg.update(tb.glyphs)
			else: raise
	for ki in font["GPOS"].table.LookupList.Lookup:
		for st in ki.SubTable:
			if st.LookupType==9:
				stbl=st.ExtSubTable
			else:
				stbl=st
			lktp=stbl.LookupType
			if lktp==1:
				coverage=stbl.Coverage
				coverage.glyphs=[g for g in coverage.glyphs if g in usedg]
			elif lktp==2:
				coverage=stbl.Coverage
				coverage.glyphs=[g for g in coverage.glyphs if g in usedg]
				if stbl.Format==1:
					for pair in stbl.PairSet:
						pair.PairValueRecord=[vr for vr in pair.PairValueRecord if vr.SecondGlyph in usedg]
				elif stbl.Format==2:
					stbl.ClassDef1.classDefs={cld:stbl.ClassDef1.classDefs[cld] for cld in stbl.ClassDef1.classDefs.keys() if cld in usedg}
					stbl.ClassDef2.classDefs={cld:stbl.ClassDef2.classDefs[cld] for cld in stbl.ClassDef2.classDefs.keys() if cld in usedg}
			elif lktp==4:
				markcoverage=stbl.MarkCoverage
				markcoverage.glyphs=[g for g in markcoverage.glyphs if g in usedg]
				basecoverage=stbl.BaseCoverage
				basecoverage.glyphs=[g for g in basecoverage.glyphs if g in usedg]
			else:
				raise
	
	nnnd=list()
	for fl in font.getGlyphOrder():
		if fl in usedg or fl in ('.notdef', '.null', 'nonmarkingreturn', 'NULL', 'NUL'):
			nnnd.append(fl)
		else:
			if 'VORG' in font and fl in font['VORG'].VOriginRecords:
				del font['VORG'].VOriginRecords[fl]
			if 'gvar' in font and fl in font['gvar'].variations:
				del font['gvar'].variations[fl]
			del font['hmtx'][fl]
			del font['vmtx'][fl]
	if 'CFF ' in font:
		subcff(font['CFF '], set(nnnd))
	elif 'CFF2' in font:
		subcff(font['CFF2'], set(nnnd))
	elif 'glyf' in font:
		font['glyf'].glyphs={g:font['glyf'].glyphs[g] for g in set(nnnd)}
	font.setGlyphOrder(nnnd)

def getother(font2, repdict):
	print('Processing...')
	if 'CFF ' in font or 'CFF2' in font:
		if 'CFF2' in font:
			cff=font['CFF2'].cff
			cff2=font2['CFF2'].cff
		else:
			cff=font['CFF '].cff
			cff2=font2['CFF '].cff
		cff2.desubroutinize()
		for fontname in cff.keys():
			fontsub=cff[fontname]
			cs=fontsub.CharStrings
			for fontname2 in cff2.keys():
				fontsub2=cff2[fontname2]
				cs2=fontsub2.CharStrings
				for gl in repdict.keys():
					cs[gl]=cs2[repdict[gl]]
					font['hmtx'][gl]=font2['hmtx'][repdict[gl]]
					font['vmtx'][gl]=font2['vmtx'][repdict[gl]]
					if 'VORG' in font and 'VORG' in font2:
						if repdict[gl] in set(font2['VORG'].VOriginRecords.keys()):
							font['VORG'].VOriginRecords[gl]=font2['VORG'].VOriginRecords[repdict[gl]]
						elif gl in set(font['VORG'].VOriginRecords.keys()):
							del font['VORG'].VOriginRecords[gl]
	elif 'glyf' in font:
		for gl in repdict.keys():
			font['glyf'].glyphs[gl]=font2['glyf'].glyphs[repdict[gl]]
			font['hmtx'][gl]=font2['hmtx'][repdict[gl]]
			font['vmtx'][gl]=font2['vmtx'][repdict[gl]]
			font['gvar'].variations[gl]=font2['gvar'].variations[repdict[gl]]
			if 'VORG' in font:
				font['VORG'].VOriginRecords[gl]=font2['VORG'].VOriginRecords[repdict[gl]]
	else:
		raise
def merge(ft):
	font2=TTFont(ft)
	cmap2=font2.getBestCmap()
	cmap=font.getBestCmap()
	gtog=dict()

	cnsp='写泻画瑶'#恋峦蛮挛栾滦弯湾
	for ncd in cmap2.keys():
		if ncd==0x20 or ncd not in cmap:continue
		chn=chr(ncd)
		print('Find', chn)
		if chn in cnsp:
			g1=glfrloc(cmap[ncd], loczhs)
		else:
			g1=cmap[ncd]
		g2=cmap2[ncd]
		gtog[g1]=g2
	loczhsnew=getloclk(font2, 'ZHS')
	for chn in '禅遥':
		print('Find', chn)
		g1=glfrloc(cmap[ord(chn)], loczhs)
		g2=glfrloc(cmap2[ord(chn)], loczhsnew)
		gtog[g1]=g2

	getother(font2, gtog)
	font2.close()

def cksploc():
	cmap=font.getBestCmap()
	spdic={cmap[ord(ch)]:glfrloc(cmap[ord(ch)], loczhs) for ch in simpcn}
	for lan in ['ZHT', 'ZHH']:
		for lki in locllki(font["GSUB"], lan):
			for st in font["GSUB"].table.LookupList.Lookup[lki].SubTable:
				if st.LookupType==7 and st.ExtSubTable.LookupType==1:
					tabl=st.ExtSubTable.mapping
				elif st.LookupType==1:
					tabl=st.mapping
				else:
					continue
				for spgs in spdic:
					if spgs in tabl:
						tabl[spgs]=spdic[spgs]

def changeloc(loctg):
	lkzhs=locllki(font["GSUB"], 'ZHS')
	lkzht=locllki(font["GSUB"], 'ZHT')
	lkzhh=locllki(font["GSUB"], 'ZHH')
	lkzhk=locllki(font["GSUB"], 'KOR')
	lkzhj=locllki(font["GSUB"], 'JAN')

	newjpft=[lkzhj[0]-1, lkzhj[0]]
	newjp=dict()
	for st in font["GSUB"].table.LookupList.Lookup[lkzhs[0]].SubTable:
		if st.LookupType==7: stbl=st.ExtSubTable
		else: stbl=st
		dicst=stbl.mapping
		oldsc={s:dicst[s] for s in dicst}
	for st in font["GSUB"].table.LookupList.Lookup[lkzht[0]].SubTable:
		if st.LookupType==7: stbl=st.ExtSubTable
		else: stbl=st
		dicst=stbl.mapping
		oldtc={s:dicst[s] for s in dicst}
	for st in font["GSUB"].table.LookupList.Lookup[lkzhh[0]].SubTable:
		if st.LookupType==7: stbl=st.ExtSubTable
		else: stbl=st
		dicst=stbl.mapping
		oldhc={s:dicst[s] for s in dicst}
	for st in font["GSUB"].table.LookupList.Lookup[lkzhk[0]].SubTable:
		if st.LookupType==7: stbl=st.ExtSubTable
		else: stbl=st
		dicst=stbl.mapping
		oldkc={s:dicst[s] for s in dicst}

	cmap=font.getBestCmap()
	if loctg=='ZHS':
		for k in list(oldtc.keys()):
			if k in oldsc:
				oldtc[oldsc[k]]=oldtc[k]
		for k in list(oldhc.keys()):
			if k in oldsc:
				oldhc[oldsc[k]]=oldhc[k]
		for k in list(oldsc.keys()):
			if k in cmap.values():
				newjp[oldsc[k]]=k
		for k in newjp.keys():
			for lcs in (oldtc, oldhc, oldkc):
				if k not in lcs.keys() and k not in lcs.values():
					lcs[k]=newjp[k]
	elif loctg=='ZHT':
		for k in list(oldsc.keys()):
			if k in oldtc:
				oldsc[oldtc[k]]=oldsc[k]
		for k in list(oldhc.keys()):
			if k in oldtc:
				oldhc[oldtc[k]]=oldhc[k]
		for k in list(oldtc.keys()):
			if k in cmap.values():
				newjp[oldtc[k]]=k
		for k in newjp.keys():
			for lcs in (oldsc, oldhc, oldkc):
				if k not in lcs.keys() and k not in lcs.values():
					lcs[k]=newjp[k]
	
	ftl, lkl=list(), list()
	for sr in font["GSUB"].table.ScriptList.ScriptRecord:
		for lsr in sr.Script.LangSysRecord:
			if lsr.LangSysTag.strip()=='JAN':
				ftl+=lsr.LangSys.FeatureIndex
	for ki in ftl:
		ftg=font["GSUB"].table.FeatureList.FeatureRecord[ki].FeatureTag
		if ftg=='locl':
			font["GSUB"].table.FeatureList.FeatureRecord[ki].Feature.LookupListIndex=newjpft

	setpun(simpcn, loczhs)
	if loctg=='ZHS':
		setpun(pzhs, loczhs)
	elif loctg=='ZHT':
		setpun(pzht, loczht)
	elif loctg=='ZHH':
		setpun(pzht, loczhh)

	if loctg=='ZHS': lkps=(oldtc, oldhc, newjp, oldkc)
	elif loctg=='ZHT': lkps=(oldsc, oldhc, newjp, oldkc)
	for dcs in lkps:
		for k in list(dcs.keys()):
			if k==dcs[k]: del dcs[k]

	if loctg!='ZHT':
		for st in font["GSUB"].table.LookupList.Lookup[lkzht[0]].SubTable:
			if st.LookupType==7: stbl=st.ExtSubTable
			else: stbl=st
			stbl.mapping=oldtc
	if loctg!='ZHS':
		for st in font["GSUB"].table.LookupList.Lookup[lkzhs[0]].SubTable:
			if st.LookupType==7: stbl=st.ExtSubTable
			else: stbl=st
			stbl.mapping=oldsc
	for st in font["GSUB"].table.LookupList.Lookup[lkzhh[0]].SubTable:
		if st.LookupType==7: stbl=st.ExtSubTable
		else: stbl=st
		stbl.mapping=oldhc
	for st in font["GSUB"].table.LookupList.Lookup[newjpft[0]].SubTable:
		if st.LookupType==7: stbl=st.ExtSubTable
		else: stbl=st
		stbl.mapping=newjp
	for st in font["GSUB"].table.LookupList.Lookup[lkzhk[0]].SubTable:
		if st.LookupType==7: stbl=st.ExtSubTable
		else: stbl=st
		stbl.mapping=oldkc

	dfltvt(loctg)
def setpun(pzh, loczh):
	pg=glfrtxt(pzh)
	rplg=dict()
	
	for g1 in pg:
		assert g1 not in rplg, g1
		g2=glfrloc(g1, loczh)
		if g2: rplg[g1]=g2
	glyrepl(rplg)

	return
def dfltvt(lng):
	for posub in ('GSUB', 'GPOS'):
		vtzh=list()
		for sr in font[posub].table.ScriptList.ScriptRecord:
			for lsr in sr.Script.LangSysRecord:
				if lsr.LangSysTag.strip()==lng:
					for ki in lsr.LangSys.FeatureIndex:
						if vtzh: break
						if font[posub].table.FeatureList.FeatureRecord[ki].FeatureTag=='vert':
							vtzh=font[posub].table.FeatureList.FeatureRecord[ki].Feature.LookupListIndex
		for sr in font[posub].table.ScriptList.ScriptRecord:
			for lsr in sr.Script.DefaultLangSys.FeatureIndex:
				if font[posub].table.FeatureList.FeatureRecord[lsr].FeatureTag=='vert':
					font[posub].table.FeatureList.FeatureRecord[lsr].Feature.LookupListIndex=vtzh
					break
		for sr in font[posub].table.ScriptList.ScriptRecord:
			for lsr in sr.Script.DefaultLangSys.FeatureIndex:
				if font[posub].table.FeatureList.FeatureRecord[lsr].FeatureTag=='locl':
					font[posub].table.FeatureList.FeatureRecord[lsr].Feature.LookupListIndex.clear()
					break

def rmloc():
	loclks, locfts=list(), list()
	for i in range(len(font["GSUB"].table.FeatureList.FeatureRecord)):
		if font["GSUB"].table.FeatureList.FeatureRecord[i].FeatureTag=='locl':
			loclks+=font["GSUB"].table.FeatureList.FeatureRecord[i].Feature.LookupListIndex
			locfts.append(i)
	loclks=list(set(loclks))
	loclks.sort(reverse=True)
	locfts=list(set(locfts))
	locfts.sort(reverse=True)
	for i in locfts: rmft(font, 'GSUB', i)
	for i in loclks: rmlk(font, 'GSUB', i)
	for posub in ('GSUB', 'GPOS'):
		for sr in font[posub].table.ScriptList.ScriptRecord:
			sr.Script.LangSysRecord.clear()
def mulcdch():
	cmap=font.getBestCmap()
	with open(os.path.join(pydir, 'configs/mulcodechar.dt'), 'r', encoding='utf-8') as f:
		for line in f.readlines():
			litm=line.split('#')[0].strip()
			if '-' not in litm: continue
			s, t=litm.split(' ')[0].split('-')
			s, t=s.strip(), t.strip()
			if s and t and s!=t and ord(t) in cmap:
				print('Processing '+s+'-'+t)
				setcg(ord(s), cmap[ord(t)])

def uvsnone(font, nonone):
	cmap=font.getBestCmap()
	for table in font["cmap"].tables:
		if table.format==14:
			for vsl in table.uvsDict.keys():
				newl=list()
				for cg in table.uvsDict[vsl]:
					if cg[1]==None and nonone:
						newl.append((cg[0], cmap[cg[0]]))
					elif cg[0] in cmap and cg[1]==cmap[cg[0]] and not nonone:
						newl.append((cg[0], None))
					else:
						newl.append((cg[0], cg[1]))
				table.uvsDict[vsl]=newl
def getuvs(cmap):
	nuv=dict()
	for table in cmap.tables:
		if table.format==14:
			for vsl in table.uvsDict.keys():
				for cg in table.uvsDict[vsl]:
					if cg[0] not in nuv:
						nuv[cg[0]]=dict()
					nuv[cg[0]][vsl]=cg[1]
	return nuv

print('*'*50)
print('====Build Fonts====\n')
infile=sys.argv[1]
subfl=sys.argv[2]
outfile=sys.argv[3]

pen='"\'—‘’‚“”„‼⁇⁈⁉⸺⸻'
pzhs='·’‘”“•≤≥≮≯！：；？'+pen
pzht='·’‘”“•、。，．'+pen
simpcn='残浅践惮禅箪蝉径茎滞遥瑶写泻画'#恋峦蛮挛栾滦弯湾#変蒋将与弥称

font=TTFont(infile)
fpsn=font["name"].getDebugName(6)

cffinf()
uvsnone(font, True)
newmap=dict()

print('Getting the localized lookups table...')
lockor, loczhs, loczht, loczhh=getloclk(font, 'KOR'), getloclk(font, 'ZHS'), getloclk(font, 'ZHT'), getloclk(font, 'ZHH')
locglrpl(newmap)
print('Getting uvs...')
uvdic=getuvs(font['cmap'])
print('Processing locl Variant ...')
locvar(newmap)
print('Processing uvs glyphs...')
setuvs(newmap, uvdic)
print('Processing uvs Variant...')
uvsvar(newmap, uvdic)
print('Processing radicals...')

for c, g in newmap.items():
	setcg(font['cmap'], c, g)

ckdlg()
print('Getting glyphs from other fonts...')
merge(subfl)

cksploc()

print('Checking for unused glyphs...')
subgl()
changeloc('ZHT')

uvsnone(font, False)
isvf=('gvar' in font or 'CFF2' in font) and 'fvar' in font
font['name']=mkname(cfg, font['name'], '', ithw='', isvf=isvf)
print('Saving font...')
font.save(outfile)
print('Finished!')
print('*'*50)
