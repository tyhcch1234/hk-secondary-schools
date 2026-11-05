import json, re, collections, random
h=open('index.html',encoding='utf-8').read()
DATA=json.loads(re.search(r'const DATA = (\[.*?\]);\n',h,re.S).group(1))

THEMES = {
 '自主學習與學習效能': ['自主學習','自學','學習效能','學習動機','學習習慣','元認知','預習','學習方法','學習技巧','主動學習','學習態度','學習能力','自我效能','成長型思維','學習者','個性化學習','學習成果','求知','樂學','善學'],
 '價值觀與品德教育': ['價值觀','品格','品德','德育','正向價值','堅毅','同理心','感恩','責任','誠信','尊重','承擔','公民','美德','品德素養'],
 '國民教育與中華文化': ['國民','國家安全','愛國','家國','國情','基本法','憲法','中華文化','國家發展','民族','傳統文化','中國歷史'],
 '身心健康與正向教育': ['身心健康','精神健康','正向教育','抗逆','幸福感','壓力','情緒','健康生活','健康校園','身心靈','運動','睡眠','正向文化','正向思維','正向人生','身心','健康','正向'],
 '閱讀氛圍': ['閱讀','書香','讀書'],
 'AI、STEM 與創科': ['STEM','STEAM','人工智能','(?<![A-Za-z])AI(?![A-Za-z])','創科','編程','電子學習','數碼','資訊科技','科學','科技','創新科技','運算思維','創客'],
 '語文能力': ['語文','英語','兩文三語','寫作','普通話','中文能力','語言能力'],
 '學與教及課程優化': ['學與教','課程','教學策略','評估','課堂','教學效能','教學法','跨課程','教學模式','學習經歷','教學設計'],
 '教師專業發展': ['教師專業','教師培訓','專業發展','教學團隊','共備','觀課','教師發展'],
 '生涯規劃與升學': ['生涯規劃','(?<!提)升學','就業','事業','職涯','出路'],
 '關愛校園與朋輩支援': ['關愛','校園文化','共融','歸屬感','師生關係','朋輩','支援網絡','扶持','凝聚力','聯繫','同行'],
 '全人發展與多元潛能': ['全人','潛能','多元發展','體藝','藝術','領袖','才能','五育','多元','視野','服務'],
 '環保與可持續發展': ['環保','可持續','綠色','節能','碳','環境','永續'],
 '家校合作': ['家長','家校'],
 '學習多樣性與特殊教育': ['學習多樣性','特殊教育','SEN','學習差異','融合教育','差異','照顧不同'],
 '資優與拔尖': ['資優','拔尖','尖子'],
}
import re as _re
def tags(t):
    out=[]
    for n,kws in THEMES.items():
        for k in kws:
            if k.startswith('(?') or k.startswith('['):
                if _re.search(k,t): out.append(n); break
            elif k in t: out.append(n); break
    return out

sh=collections.Counter(); ih=collections.Counter(); untag=[]
rows=[]
for d in DATA:
    s=set()
    for it in d['i']:
        tg=tags(it)
        if not tg: untag.append((d['n'],it))
        for t in tg: ih[t]+=1; s.add(t)
    for t in s: sh[t]+=1
    rows.append((d['n'],d['d'],d['t'],s))
tot=sum(len(d['i']) for d in DATA)
print('schools',len(DATA),'items',tot,'untagged',len(untag),f'{len(untag)/tot*100:.0f}%')
print('avg themes',round(sum(len(r[3]) for r in rows)/len(rows),2))
for t,c in sh.most_common(): print(f'{t:16s}{c:4d} 校  {c/len(DATA)*100:5.1f}%   項 {ih[t]}')
print('--- combos')
pairs=collections.Counter()
for n,d,t,s in rows:
    sl=sorted(s)
    for i in range(len(sl)):
        for j in range(i+1,len(sl)): pairs[(sl[i],sl[j])]+=1
for (a,b),c in pairs.most_common(6): print(f'  {a} + {b}: {c}')
print('--- no theme schools', sum(1 for r in rows if not r[3]))
random.seed(2)
for t in ['生涯規劃與升學','全人發展與多元潛能']:
    items=[(d['n'],it) for d in DATA for it in d['i'] if t in tags(it)]
    print('##',t,len(items))
    for n,it in random.sample(items,4): print('   ',n,'|',it[:70])
