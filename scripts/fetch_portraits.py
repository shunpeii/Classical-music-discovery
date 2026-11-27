import json, pathlib, urllib.request, urllib.parse, time, re, html
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'public/images/composers'
OUT.mkdir(parents=True,exist_ok=True)
sources=json.loads((ROOT/'scripts/portrait_sources.json').read_text())
master=ROOT/'public/data/master/composers.json'
composers=json.loads(master.read_text())
credits=OUT/'credits.json'
old=json.loads(credits.read_text()) if credits.exists() else {}
def get(url,params=None):
    if params: url+='?'+urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'OpusComposerCatalogue/1.0 (https://github.com/shunpeii/Classical-music-discovery)'}),timeout=45) as response:
                return response.read()
        except Exception:
            if attempt==2: raise
            time.sleep(5*(attempt+1))
def api(host,**params):
    return json.loads(get('https://'+host+'/w/api.php',dict(action='query',format='json',formatversion=2,**params)))['query']['pages'][0]
def plain(value):
    return html.unescape(re.sub('<[^>]*>','',value))
failed=[]
for c in composers:
    key=c['id']
    if key in old and c.get('portrait') and (ROOT/'public'/c['portrait']).exists(): continue
    try:
        page=api('en.wikipedia.org',titles=sources[key],redirects=1,prop='pageprops')
        qid=page['pageprops']['wikibase_item']
        entity=json.loads(get('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json'))['entities'][qid]
        files=[v['mainsnak']['datavalue']['value'] for v in entity['claims']['P18'] if 'datavalue' in v['mainsnak']]
        for file in files:
            info=api('commons.wikimedia.org',titles='File:'+file,redirects=1,prop='imageinfo',iiprop='url|extmetadata|mime',iiurlwidth=400)['imageinfo'][0]
            m=info['extmetadata']
            val=lambda k:plain(m.get(k,{}).get('value',''))
            license=val('LicenseShortName')
            if not (license.startswith(('CC BY ','CC BY-SA ','CC0','Public domain','PDM')) or val('Copyrighted')=='False'): continue
            data=get(info.get('thumburl',info['url']))
            if data.startswith(b'\xff\xd8'): ext='jpg'
            elif data.startswith(b'\x89PNG'): ext='png'
            else: continue
            rel='images/composers/'+key+'.'+ext
            (ROOT/'public'/rel).write_bytes(data)
            c['portrait']=rel
            old[key]={'file':file,'source':info['descriptionurl'],'artist':val('Attribution') or val('Artist'),'license':license,'licenseUrl':val('LicenseUrl')}
            print(key,license,flush=True)
            break
        else: raise ValueError('No eligible portrait')
    except Exception as e:
        failed.append(key)
        print(key,str(e),flush=True)
    time.sleep(1)
master.write_text(json.dumps(composers,ensure_ascii=False,indent=2)+'\n')
credits.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
print('Missing:',failed)
if failed: raise SystemExit(1)
