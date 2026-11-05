import json, re, os

DOTS=re.compile(r'(\.{3,}|…{2,}|·{3,}|_{3,})')
TOCISH=re.compile(r'(\.{3,}|…{2,}).*\d+\s*$')
ANCHOR=re.compile(r'關注事項\s*[（(]?\s*([一二三四五1-5])\s*[)）]?\s*[：:、.]?\s*(.*)')
ANCHOR2=re.compile(r'^(?:[IVX]{1,4}|\d{1,2})\s*[\.、]\s*關注事項\s*[：:]\s*(.+)')
ENG=re.compile(r'Major\s+Concern[s]?\s*(\d)?\s*[:\-]?\s*(.*)',re.I)
OUT_MARK=re.compile(r'^(成效|成果|成就|預期成果|評估結果|表現|成效評估|檢討)')
REF_MARK=re.compile(r'^(反思|回饋|跟進|建議|改善)')
STOP=re.compile(r'^(關注事項|目標|策略|成功準則|評估方法|時間表|負責人|所需資源|開支|財政)')
JUNK=re.compile(r'^(Goals|Strategies|Outcomes|Reflections|Feedback|Targets|成功準則|評估方法|時間表|負責人|目標\s*策略|關注事項\s*$)',re.I)
PAGEHDR=re.compile(r'(學校報告|周年報告|學校周年報告).{0,20}(P\.?\s*\d+|20\d\d)')

def lines_of(text):
    out=[]
    for raw in text.split('\n'):
        l=raw.replace('\u3000',' ').strip()
        l=re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])','',l)
        l=re.sub(r'\s{2,}',' ',l)
        if not l: continue
        if TOCISH.search(l): continue
        if len(DOTS.findall(l))>=1 and DOTS.sub('',l).strip()=='' : continue
        if re.fullmatch(r'[\d\s\.\-—_·]+', l): continue
        if len(l)<2: continue
        out.append(l)
    return out

def join_frag(ls):
    out=[]
    for l in ls:
        if out and (len(out[-1])<18 and not re.search(r'[。；;：:]$', out[-1])):
            sep=' ' if re.search(r'[A-Za-z0-9,]$', out[-1]) and re.match(r'[A-Za-z0-9]', l) else ''
            out[-1]+=sep+l
        else:
            out.append(l)
    return out

JUNKTITLE=re.compile(r'^[\(（]?(achievements?|reflections?|feedback|outcomes?|evaluation|檢討|反思|成就|成效)[\)）]?$',re.I)

def sents(ls, maxn=3, maxlen=120):
    # join wrapped latin lines into paragraphs first
    merged=[]
    buf=''
    for l in ls:
        if all(ord(c)<128 or c in ' .,;:()' for c in l):
            buf=(buf+' '+l).strip()
            if l.rstrip().endswith(('.','!','?')):
                merged.append(buf); buf=''
        else:
            if buf: merged.append(buf); buf=''
            merged.append(l)
    if buf: merged.append(buf)
    res=[]
    for l in merged:
        l=re.sub(r'^[\-•·◆▪\uf06c\uf0b7\uf09f\s]+','',l)
        l=re.sub(r'^\d+(\.\d+)*[\.、\)）]?\s*','',l)
        if JUNK.search(l) or PAGEHDR.search(l): continue
        parts=re.split(r'(?<=[。；;！？])', l) if re.search(r'[\u4e00-\u9fff]', l) else re.split(r'(?<=[.!?])\s+', l)
        for s in parts:
            s=s.strip(' ，,、：:')
            if len(s)<10: continue
            if JUNK.search(s): continue
            if len(s)>maxlen: s=s[:maxlen].rstrip('，,')+'…'
            res.append(s)
            if len(res)>=maxn: return res
    return res

def clean_title(t):
    t=re.sub(r'P\.?\s*\d+\s*[~\-–]\s*P?\.?\s*\d+','',t)
    t=re.sub(r'[\s\.·]*\d{1,3}\s*([-~–]\s*\d{1,3})?\s*$','',t)
    return t.strip(' ：:、.-~')

def parse(text):
    ls=join_frag(lines_of(text))
    idx=[(i,m) for i,l in enumerate(ls) for m in [ANCHOR.search(l)] if m]
    if not idx:
        idx=[(i,m) for i,l in enumerate(ls) for m in [ANCHOR2.search(l)] if m]
    if not idx:
        # english fallback
        idx=[(i,m) for i,l in enumerate(ls) for m in [ENG.search(l)] if m]
    if not idx: return []
    raw=[]
    for k,(i,m) in enumerate(idx[:30]):
        if m.re is ANCHOR2:
            num=''; rest=(m.group(1) or '').strip(' ：:、.')
        else:
            num=m.group(1); rest=(m.group(2) or '').strip(' ：:、.')
        title=rest
        if len(title)<6 and i+1<len(ls) and len(ls[i+1])<40 and not STOP.match(ls[i+1]):
            title=ls[i+1]
        title=re.sub(r'^\d+(\.\d+)*[\.、\)）]?\s*','',title)
        title=clean_title(title)[:60]
        if JUNKTITLE.match(title): title=''
        if len(title) < 6:
            for nxt in ls[i+1:i+3]:
                if len(nxt) > 8 and not STOP.match(nxt) and not re.match(r'^(Goals|Strategies|Outcomes|Targets)', nxt, re.I):
                    title=clean_title(nxt)[:60]; break
        end=idx[k+1][0] if k+1<len(idx) else min(len(ls), i+60)
        chunk=ls[i+1:end]
        oi=None
        for j,l in enumerate(chunk):
            if OUT_MARK.search(l) or re.match(r'^(成就|成效|成果)', l) or ('成效' in l[:10] or '成就' in l[:10]):
                oi=j; break
            if len(l)>26 and ('成效' in l[:26] or '成就' in l[:26]):
                oi=j; break
        content=chunk[:oi] if oi is not None else chunk[:10]
        outcome=[]
        if oi is not None:
            first=re.sub(r'^(成就|成效|成果|預期成果|評估結果|檢討)\s*[：:\d\.]*\s*','',chunk[oi])
            if first: outcome.append(first)
            for l in chunk[oi+1:]:
                if REF_MARK.search(l) and len(l)<=20: break
                outcome.append(l)
        body_chars=sum(len(x) for x in chunk)
        raw.append({
            'no': num,
            'title': title or '關注事項',
            'content': sents(content,2,110),
            'outcome': sents(outcome,2,130),
            'body': body_chars,
        })
    best={}
    for b in raw:
        k=(b['no'] or '')+clean_title(b['title'])[:14]
        if k not in best or b['body']>best[k]['body']: best[k]=b
    blocks=[b for b in best.values() if b['body']>=120]
    blocks.sort(key=lambda b: (b['no'] or '9'))
    return blocks[:5]

if __name__=='__main__':
    idx=json.load(open('data/reports/pdf_index.json'))
    rows={r['id']:r for r in json.load(open('data/schools.json'))}
    out={}
    for sid,kept in idx.items():
        yrs=[]
        for k in sorted(kept,key=lambda x:x['y']):
            p=f"data/reports/txt/{sid}_{k['y']}.txt"
            if not os.path.exists(p): continue
            b=parse(open(p,encoding='utf-8').read())
            def cjk(x): return any('\u4e00'<=c<='\u9fff' for c in x)
            zh=[x for x in b if cjk(x['title']+''.join(x['outcome']+x['content']))]
            if zh: yrs.append({'y':k['y'],'u':k['u'],'b':zh})
            elif b: yrs.append({'y':k['y'],'u':k['u'],'b':b,'en':True})
        if yrs: out[sid]=yrs
    json.dump(out,open('data/reports/parsed2.json','w'),ensure_ascii=False,indent=1)
    print('schools',len(out),'school-years',sum(len(v) for v in out.values()),
          'blocks',sum(len(y['b']) for v in out.values() for y in v))
