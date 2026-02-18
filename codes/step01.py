import os, json, sys
from fontTools.ttLib import TTFont, newTable
from .hpsh import *

SCRIPT_DIR=os.path.abspath(os.path.dirname(__file__))
CONFIG_JSON='config.json'
SOURCEHAN_CFG_JSON='sourcehan.json'
UVS_CFG_JSON='uvs.json'

p_en='"\'—‘’‚“”„‼⁇⁈⁉⸺⸻'
p_zhs='·’‘”“•≤≥≮≯！：；？'+p_en
p_zht='·’‘”“•、。，．'+p_en
simpch='蒋将残浅践惮禅箪蝉径茎滞遥瑶写泻画'#恋峦蛮挛栾滦弯湾#変与弥称

JP_VARIANTS=[
	('𰰨', '芲'), ('𩑠', '頙'), ('鄉', '鄕'), ('唧', '喞'), ('𥄳', '眔')
]
RADICAL_VARIANTS=[
	('⽉', '月'), ('⻁', '虎'), ('⾳', '音'), ('⿓', '龍'),
	('⼾', '戶'), ('飠', '𩙿'), ('礻', '⺬')
]
LOCL_SC_VARIANTS=[("𫜹", "彐"), ("𣽽", "潸")]
UVS_MULTIPLE=[
	('⺼', '月', 'E0100'), ('𱍐', '示', 'E0100'), ('䶹', '屮', 'E0101'),
	('𠾖', '器', 'E0100'), ('𡐨', '壄', 'E0100'), ('𤥨', '琢', 'E0101'),
	('𦤀', '臭', 'E0100'), ('𨺓', '隆', 'E0100'), ('𫜸', '叱', 'E0101'),
	('暨', '曁', 'E0101'), ('廄', '廏', 'E0101'), ('倂', '併', 'E0101')
]


LOCL_LANG_TAGS={
	"krgl": "KOR", "scgl": "ZHS", "tcgl": "ZHT", "hcgl": "ZHH"
	}

def locllki(ftgsub, lang_tag):
	ftl, lkl=list(), list()
	for sr in ftgsub.table.ScriptList.ScriptRecord:
		for lsr in sr.Script.LangSysRecord:
			if lsr.LangSysTag.strip()==lang_tag:
				ftl+=lsr.LangSys.FeatureIndex
	for ki in ftl:
		ftg=ftgsub.table.FeatureList.FeatureRecord[ki].FeatureTag
		if ftg=='locl':
			lkl+=ftgsub.table.FeatureList.FeatureRecord[ki].Feature.LookupListIndex
	return sorted(set(lkl))

def getloclk(font, lang_tag):
	locdics=list()
	for lki in locllki(font["GSUB"], lang_tag):
		locrpl=dict()
		for st in font["GSUB"].table.LookupList.Lookup[lki].SubTable:
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

def uvsfill(font, isfill):
	cmap=font.getBestCmap()
	for table in font["cmap"].tables:
		if table.format == 14:
			for selector, records in list(table.uvsDict.items()):
				new_records=[]
				for code, glyph in records:
					if isfill and glyph is None:
						new_records.append((code, cmap.get(code)))
					elif not isfill and code in cmap and glyph == cmap[code]:
						new_records.append((code, None))
					else:
						new_records.append((code, glyph))
				table.uvsDict[selector]=new_records


def load_json(js_name):
	with open(os.path.join(SCRIPT_DIR, 'configs', js_name), "r", encoding="utf-8") as f:
		return json.load(f)

def getuvs(cmap):
	uvs_map={}
	for subtable in cmap.tables:
		if subtable.format == 14:
			for selector, records in subtable.uvsDict.items():
				for code, glyph in records:
					if code not in uvs_map:
						uvs_map[code]={}
					uvs_map[code][selector]=glyph
	return uvs_map

def cffinf(font, cfg, fpsn):
	if 'CFF ' in font:
		cff=font['CFF '].cff
		fmln=cfg['Name']
		for ss in ('Sans', 'Serif', 'Mono'):
			if ss in fpsn: fmln+=' '+ss
		psn=fmln.replace(' ', '')
		pso=cff.fontNames[0].split('-')[0]
		fmlo=cff[0].FamilyName
		cff.fontNames[0]=cff.fontNames[0].replace(pso, psn)
		cff[0].FamilyName=fmln
		cff[0].FullName=cff[0].FullName.replace(fmlo, fmln)
		cff[0].Notice=cfg['Copyright'].format(name=cfg['Name'], year=datetime.now().year)
		cff[0].CIDFontVersion=float(cfg['Version'])
		for dic in cff[0].FDArray:
			dic.FontName=dic.FontName.replace(pso, psn)

def locglrpl(font, new_map, locl_data):
	locgls=dict()
	shset=load_json(SOURCEHAN_CFG_JSON)
	cmap=font.getBestCmap()
	for key, lang_tag in LOCL_LANG_TAGS.items():
		for ch in shset[key]:
			code=ord(ch)
			if code not in cmap: continue
			g1=cmap[code]
			assert g1 not in locgls, f"Code point U+{code:04X} ({ch}) already remapped"
			g2=glfrloc(g1, locl_data[lang_tag])
			if g2: locgls[g1]=g2
	for code in cmap:
		if cmap[code] in locgls:
			assert code not in new_map, f"Code point U+{code:04X} ({chr(cd)}) already remapped"
			new_map[code]=locgls[cmap[code]]

def locvar(font, new_map, locl_data):
	cmap=font.getBestCmap()
	for ch1, ch2 in JP_VARIANTS + RADICAL_VARIANTS:
		code1, code2=ord(ch1), ord(ch2)
		if code2 in cmap:
			assert code1 not in new_map, f"Variant {ch1} already mapped"
			new_map[code1]=cmap[code2]
	for ch1, ch2 in LOCL_SC_VARIANTS:
		code1, code2=ord(ch1), ord(ch2)
		if code2 in cmap:
			assert code1 not in new_map, f"Variant {ch1} already mapped"
			g2=glfrloc(cmap[code2], locl_data['ZHS'])
			if g2:
				new_map[code1]=g2

def setuvs(new_map, uvs_dict):
	uvs_cfg=load_json(UVS_CFG_JSON)
	tv={ord(ch): int(uv, 16) for ch, uv in uvs_cfg.items()}
	for c, sel in uvs_dict.items():
		if c in tv and tv[c] in sel:
			g=sel[tv[c]]
			if c in new_map:
				if new_map[c]==g: continue
				else: raise RuntimeError(f"UVS mapped diffent glyph at {chr(c)} U+{c:04X}: {new_map[c]} vs {g}")
			new_map[c]=g

	for ch1, ch2, ch3 in UVS_MULTIPLE:
		u1, u2, sel=ord(ch1), ord(ch2), int(ch3, 16)
		if u2 in uvs_dict and sel in uvs_dict[u2]:
			assert u1 not in new_map, f"UVS variant {ch2} already mapped"
			new_map[u1]=uvs_dict[u2][sel]

def getother(font, font2, repdict):
	print('Processing glyphs from other fonts.')
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
				for g1,g2 in repdict.items():
					cs[g1]=cs2[g2]
	for g1,g2 in repdict.items():
		for xmtx in ['hmtx', 'vmtx']:
			if xmtx in font and xmtx in font2:
				font[xmtx][g1] = font2[xmtx][g2]
		if 'VORG' in font and 'VORG' in font2:
			if g2 in set(font2['VORG'].VOriginRecords.keys()):
				font['VORG'].VOriginRecords[g1]=font2['VORG'].VOriginRecords[g2]
			elif g1 in set(font['VORG'].VOriginRecords.keys()):
				del font['VORG'].VOriginRecords[gl]
		if 'glyf' in font and 'glyf' in font2:
			font['glyf'].glyphs[g1]=font2['glyf'].glyphs[g2]
		if 'gvar' in font and 'gvar' in font2:
			font['gvar'].variations[g1]=font2['gvar'].variations[g2]


def newglyph(font, filenew, locl_data):
	cmap=font.getBestCmap()
	print('Getting glyphs from  new.')
	if os.path.isfile(filenew):
		with TTFont(filenew) as font2:
			getnew=dict()
			cmap2=font2.getBestCmap()
			cnsp='写泻画瑶'#恋峦蛮挛栾滦弯湾
			for c, g2 in cmap2.items():
				if c==0x20 or c not in cmap:continue
				ch=chr(c)
				print(f"Found new character: {ch} (U+{c:04X})")
				if ch in cnsp: g1=glfrloc(cmap[c], locl_data['ZHS'])
				else: g1=cmap[c]
				getnew[g1]=g2
			loczhsnew=getloclk(font2, 'ZHS')
			for ch in '禅遥':
				print(f"Found locl character: {ch} (U+{c:04X})")
				g1=glfrloc(cmap[ord(ch)], locl_data['ZHS'])
				g2=glfrloc(cmap2[ord(ch)], loczhsnew)
				getnew[g1]=g2
			getother(font, font2, getnew)
			font2.close()
			for table in font['cmap'].tables:
				if table.format==14:
					for uv in table.uvsDict:
						table.uvsDict[uv]=[cg for cg in table.uvsDict[uv] if cg[1] not in getnew.values()]

def ckdlg(font, uvs_dict):
	rplg=dict()
	for ch in '成':
		rplg[uvs_dict[ord(ch)][0xE0100]]=uvs_dict[ord(ch)][0xE0101]
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

def rmfttgs(font, tgs):
	for posub in ('GSUB', 'GPOS'):
		keepft, keeplk=set(), set()
		ftrcd=font[posub].table.FeatureList.FeatureRecord
		lklst=font[posub].table.LookupList.Lookup
		for sr in font[posub].table.ScriptList.ScriptRecord:
			for j in sr.Script.DefaultLangSys.FeatureIndex:
				if ftrcd[j].FeatureTag not in tgs and ftrcd[j].Feature.LookupListIndex:
					keepft.add(j)
			for lsr in sr.Script.LangSysRecord:
				for j in lsr.LangSys.FeatureIndex:
					if ftrcd[j].FeatureTag not in tgs and ftrcd[j].Feature.LookupListIndex:
						keepft.add(j)
		for i in keepft:
			for j in ftrcd[i].Feature.LookupListIndex:
				keeplk.add(j)
		if posub=='GSUB':
			for lkp in lklst:
				for st in lkp.SubTable:
					if st.LookupType in (5, 6):
						if hasattr(st, 'SubstLookupRecord'):
							for sbrcd in st.SubstLookupRecord:
								keeplk.add(sbrcd.LookupListIndex)
						if hasattr(st, 'ChainSubClassSet'):
							for rul in st.ChainSubClassSet:
								if hasattr(rul, 'ChainSubClassRule'):
									for subr in rul.ChainSubClassRule:
										for sbrcd in subr.SubstLookupRecord:
											keeplk.add(sbrcd.LookupListIndex)
		locfts={i for i in range(len(ftrcd)) if i not in keepft}
		loclks={i for i in range(len(lklst)) if i not in keeplk}
		locfts=sorted(locfts, reverse=True)
		loclks=sorted(loclks, reverse=True)
		for i in locfts: rmft(font, posub, i)
		for i in loclks: rmlk(font, posub, i)

def subgl(font):
	cmap=font.getBestCmap()
	hangul=set()
	hangul.update(range(0x1100, 0x11FF+1))
	hangul.update(range(0x3130, 0x318F+1))
	hangul.update(range(0xA960, 0xA97F+1))
	hangul.update(range(0xAC00, 0xD7FF+1))
	hangul.update(range(0xFFA0, 0xFFDF+1))
	hangul.update(range(0x3200, 0x32FF+1))

	for table in font["cmap"].tables:
		table.cmap={code:table.cmap[code] for code in table.cmap if code not in hangul}
	cmap=font.getBestCmap()

	dropfts=['nlck', 'jp78', 'jp83', 'jp90', 'calt', 'ljmo', 'tjmo', 'vjmo', 'aalt']
	rmfttgs(font, dropfts)

	rmlkre=set()
	for i, lk in enumerate(font["GSUB"].table.LookupList.Lookup):
		for st in lk.SubTable:
			if st.LookupType in (5, 6) and hasattr(st, 'SubstLookupRecord'):
				rmlkre.add(i)

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
	pungl={cmap[ord(ch)] for ch in p_zhs+p_zht+simpch if ord(ch) in cmap}
	print('Checking Lookup table...')

	loclks=set()
	for ft in font["GSUB"].table.FeatureList.FeatureRecord:
		if ft.FeatureTag=='locl':
			loclks.update(ft.Feature.LookupListIndex)
	for lki in loclks:
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

	emplk=set()
	for i, ki in enumerate(font["GSUB"].table.LookupList.Lookup):
		lnth=0
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
				lnth+=1
			elif lktp==3:
				for item in list(stbl.alternates.keys()):
					if item in usedg:
						usedg.update(set(stbl.alternates[item]))
					else:
						del stbl.alternates[item]
				lnth+=len(stbl.alternates)
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
				lnth+=len(stbl.ligatures)
			else: raise
		if lnth==0: emplk.add(i)
	for ftr in font["GSUB"].table.FeatureList.FeatureRecord:
		ftr.Feature.LookupListIndex=[idx for idx in ftr.Feature.LookupListIndex if idx not in emplk]
	rmfttgs(font, [])

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

	for table in font["cmap"].tables:
		if table.format == 14:
			uvsdata=dict()
			for selector, records in list(table.uvsDict.items()):
				new_records=[]
				for code, glyph in records:
					if glyph in nnnd:
						new_records.append((code, glyph))
				if new_records:
					uvsdata[selector]=new_records
			table.uvsDict=uvsdata

def glyrepl(font, repdic):
	for table in font["cmap"].tables:
		for cd in table.cmap:
			if table.cmap[cd] in repdic:
				table.cmap[cd]=repdic[table.cmap[cd]]
				print('Remapping', chr(cd))

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
				if st.LookupType in (5, 6):
					if hasattr(st, 'SubstLookupRecord'):
						for sbrcd in st.SubstLookupRecord:
							if sbrcd.LookupListIndex>i:
								sbrcd.LookupListIndex-=1
					if hasattr(st, 'ChainSubClassSet'):
						for rul in st.ChainSubClassSet:
							if hasattr(rul, 'ChainSubClassRule'):
								for subr in rul.ChainSubClassRule:
									for sbrcd in subr.SubstLookupRecord:
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

def cksploc(font, locl_data):
	cmap=font.getBestCmap()
	spdic={cmap[ord(ch)]:glfrloc(cmap[ord(ch)], locl_data['ZHS']) for ch in simpch}
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

def changeloc(font, locl_data, loctg):
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

	def setpun(pzh, loczh):
		pg={cmap[ord(ch)] for ch in pzh if ord(ch) in cmap}
		rplg=dict()
		
		for g1 in pg:
			assert g1 not in rplg, g1
			g2=glfrloc(g1, loczh)
			if g2: rplg[g1]=g2
		
		for table in font["cmap"].tables:
			for cd in table.cmap:
				if table.cmap[cd] in rplg:
					table.cmap[cd]=rplg[table.cmap[cd]]
					print('Remapping', chr(cd))

	setpun(simpch, locl_data['ZHS'])
	setpun(p_zhs, locl_data[loctg])

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

	for posub in ('GSUB', 'GPOS'):
		vtzh=list()
		for sr in font[posub].table.ScriptList.ScriptRecord:
			for lsr in sr.Script.LangSysRecord:
				if lsr.LangSysTag.strip()==loctg:
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

def rmloc(font):
	for posub in ('GSUB', 'GPOS'):
		keepft, keeplk=set(), set()
		ftrcd=font[posub].table.FeatureList.FeatureRecord
		lklst=font[posub].table.LookupList.Lookup
		for sr in font[posub].table.ScriptList.ScriptRecord:
			for j in sr.Script.DefaultLangSys.FeatureIndex:
				if ftrcd[j].FeatureTag!='locl':
					keepft.add(j)
			sr.Script.LangSysRecord.clear()
		for i in keepft:
			for j in ftrcd[i].Feature.LookupListIndex:
				keeplk.add(j)
		if posub=='GSUB':
			for lkp in lklst:
				for st in lkp.SubTable:
					if st.LookupType in (5, 6):
						if hasattr(st, 'SubstLookupRecord'):
							for sbrcd in st.SubstLookupRecord:
								keeplk.add(sbrcd.LookupListIndex)
						if hasattr(st, 'ChainSubClassSet'):
							for rul in st.ChainSubClassSet:
								if hasattr(rul, 'ChainSubClassRule'):
									for subr in rul.ChainSubClassRule:
										for sbrcd in subr.SubstLookupRecord:
											keeplk.add(sbrcd.LookupListIndex)
		locfts={i for i in range(len(ftrcd)) if i not in keepft}
		loclks={i for i in range(len(lklst)) if i not in keeplk}
		loclks=sorted(loclks, reverse=True)
		locfts=sorted(locfts, reverse=True)
		for i in locfts: rmft(font, posub, i)
		for i in loclks: rmlk(font, posub, i)

def mulcdch(font):
	cmap=font.getBestCmap()
	with open(os.path.join(SCRIPT_DIR, 'configs', 'mulcodechar.dt'), 'r', encoding='utf-8') as f:
		for line in f.readlines():
			litm=line.split('#')[0].strip()
			if '-' not in litm: continue
			s, t=litm.split(' ')[0].split('-')
			s, t=s.strip(), t.strip()
			if s and t and s!=t and ord(t) in cmap:
				print('Processing '+s+'-'+t)
				setcg(font['cmap'], ord(s), cmap[ord(t)])

def main(infile, subfl, outfile):
	print("*" * 50)
	print("==== Build Shanggu Fonts ====")
	print(f"Input font: {infile}")
	print(f"Input new: {subfl}")
	print(f"Output font: {outfile}")
	config=load_json(CONFIG_JSON)

	with TTFont(infile) as font:
		fpsn=font["name"].getDebugName(6)
		cffinf(font, config, fpsn)
		uvsfill(font, isfill=True)
		new_map={}
		print("Extracting locl mappings.")
		locl_data={
			lang: getloclk(font, lang)
			for lang in LOCL_LANG_TAGS.values()
		}
		print(f"Loaded locl mappings for languages: {sorted(locl_data.keys())}")
		print("Extracting uvs mappings.")
		uvs_dict=getuvs(font["cmap"])
		print("Processing locl Variant.")
		locglrpl(font, new_map, locl_data)
		print('Processing other Variant.')
		locvar(font, new_map, locl_data)
		print('Processing uvs glyphs.')
		setuvs(new_map, uvs_dict)
		print('Remapp glyphs.')
		for c, g in new_map.items():
			print(f"Remapping U+{c:04X} ({chr(c)}) to {g}")
			setcg(font['cmap'], c, g)
		print('Checking lookups.')
		ckdlg(font, uvs_dict)
		print('Getting glyphs from other fonts.')
		newglyph(font, subfl, locl_data)
		mulcdch(font)

		cksploc(font, locl_data)
		print('Checking for unused glyphs.')
		subgl(font)
		changeloc(font, locl_data, 'ZHT')

		uvsfill(font, isfill=False)
		isvf="fvar" in font
		font['name']=mkname(config, font['name'], 'nm', isvf=isvf)
		font['head'].fontRevision=float(config['Version'])
		font['OS/2'].achVendID=config['ID']
		print(f'Saving font to {outfile}')
		font.save(outfile)
		print("Done.")
		print('*'*50)
if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2], sys.argv[3])
