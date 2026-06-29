# -*- coding: utf-8 -*-
"""심야 편의점 풀버전(70컷) 비트시트 → jobs.json + lettering.json 생성기.
규약: 긍정 프롬프트에 'speech bubble' 단어 금지(빈 타원 방지). animagine 강화 negative.
샷별 IP-Adapter: wide/full → full/0.4, close/emotion → face/0.5, insert → 캐릭터 없음."""
import json, os

JIHO = "e95ac39e-6f02-412c-9a95-9a06489ae677"
YUNA = "08f8bba9-23e0-4f1e-9c6d-dd29046f6b5a"

LOC = {
 "EXT":   "exterior storefront of a brightly lit Korean convenience store at night, glowing neon sign, wet rainy street with reflections",
 "CVS":   "interior of a brightly lit Korean convenience store at night, product shelves, checkout counter, cold fluorescent lighting",
 "STREET":"empty wet city street at deep night, rain, a blinking traffic light, neon reflections on asphalt",
 "CCTV":  "a grainy black-and-white security CCTV monitor screen showing the convenience store counter area",
 "PHONE": "extreme close-up of a smartphone screen held in a hand inside a dim convenience store at night",
}
JIHO_DESC = "a tired young Korean man with short black hair wearing a gray hoodie"
YUNA_DESC = "a pale young Korean woman with long straight black hair wearing a plain white dress"
SHOT = {
 "wide":"wide establishing shot, ", "full":"full body shot, ",
 "close":"close-up shot, ", "emotion":"extreme emotional close-up of the face, ",
 "insert":"extreme close-up insert detail shot, ",
}
QUAL = ", masterpiece, best quality, highly detailed, sharp focus, intricate details, cinematic moody lighting"
NEG = ("text, speech bubble, caption, watermark, purple hair, silver highlights, oversaturated, "
       "lowres, blurry, jpeg artifacts, bad anatomy, deformed, extra fingers, speech bubble, speech balloon, "
       "manga panel, comic book, comic panel, dialogue text, japanese text, caption box, sound effect text, "
       "manga, manhwa text")

# bubble_space → (top, left, tail, max_width)  (퍼센트 문자열)
BS = {
 "tl":("6%","6%","bottom-left","52%"),  "tr":("6%","42%","bottom-right","52%"),
 "bl":("60%","6%","bottom-left","52%"),  "br":("60%","42%","bottom-right","52%"),
 "top":("7%","10%","none","80%"),        "bottom":("82%","10%","none","80%"),
 "center":("44%","15%","none","70%"),    "ml":("38%","5%","bottom-left","46%"),
}

# 각 비트: (shot, loc, char, scene_en, bspace, [ (type,speaker,text_ko), ... ], neg_extra)
B = [
 # ── ACT 1 · 설정 (1-20) ───────────────────────────────
 ("wide","EXT",None,"rain pouring over the neon storefront, no people, lonely glow, low-detail empty area at top","top",[("narration","","비 오는 날 새벽 3시. 손님은 늘 그 시간에 온다.")],"people"),
 ("wide","STREET",None,"deserted street, a single blinking traffic light, rain, low-detail empty area at top","top",[("narration","","도시가 잠든 시간.")],"people"),
 ("full","CVS","jiho","{j} slouching bored behind the counter, scrolling his phone, low-detail empty area at top-left","tl",[("thought","지호","오늘도… 조용하네.")],""),
 ("close","CVS","jiho","{j} yawning, half-lidded tired eyes, low-detail empty area at top-right","tr",[("sfx","","하아암—")],""),
 ("insert","CVS",None,"a round wall clock on the store wall reading almost three o'clock, dim","bl",[("narration","","2시 58분.")],"people"),
 ("insert","CVS",None,"humming refrigerated drink shelves glowing faint blue, still life, no person","tr",[("sfx","","위이잉—")],"people"),
 ("close","CVS","jiho","{j} glancing sideways at the clock with faint routine unease, low-detail empty area at top-left","tl",[("thought","지호","곧 3시… 그 사람 올 시간.")],""),
 ("wide","CVS",None,"the automatic glass entrance door of the store, quiet and still, low-detail empty area at top","top",[("narration","","정확히 3시.")],"people"),
 ("insert","CVS",None,"macro of the clock hands clicking onto 3:00 exactly","br",[("sfx","","딸깍.")],"people"),
 ("wide","CVS",None,"the automatic glass door sliding open, cold white mist rolling across the floor, a dark silhouette in the doorway","tr",[("sfx","","스르륵—")],"clear face, people crowd"),
 ("full","CVS","yuna","{y} stepping in slowly, backlit, head lowered so her face is hidden by her hair","top",[("narration","","그 여자가 들어왔다.")],""),
 ("close","CVS","jiho","{j} looking up with a polite work reflex, faint smile, low-detail empty area at top-right","tr",[("speech","지호","어서오세요.")],""),
 ("emotion","CVS","jiho","{j} feeling a sudden chill, his breath faintly visible, slight frown, low-detail empty area at top-left","tl",[("thought","지호","…왜 이렇게 춥지?")],""),
 ("full","CVS","yuna","{y} drifting slowly toward a small flower bucket by the shelves, silent, head down","tr",[],""),
 ("insert","CVS",None,"a single white chrysanthemum funeral flower held in a pale thin hand, cold tone","bl",[("narration","","그녀는 늘 같은 걸 산다.")],"face"),
 ("full","CVS","yuna","{y} placing the white chrysanthemum on the counter, head still lowered","bl",[("speech","손님","…이거 주세요.")],""),
 ("close","CVS","jiho","{j} ringing it up, unsettled, trying to glimpse her hidden face, low-detail empty area at top-left","tl",[("thought","지호","얼굴을… 한 번도 못 봤네.")],""),
 ("insert","CVS",None,"an old damp wrinkled thousand-won bill lying on the counter, faintly wet and cold","tr",[("narration","","그녀의 돈은 늘 축축하고 차가웠다.")],"people"),
 ("full","CVS","yuna","{y} taking the flower and turning toward the door, drifting away without a word","tr",[("sfx","","스르륵—")],""),
 ("wide","EXT",None,"the glass door closing, the white-dress figure dissolving into the rainy dark outside, low-detail empty area at top","top",[("narration","","…오늘도 갔다.")],""),
 # ── ACT 2 · 상승 (21-48) ──────────────────────────────
 ("insert","CVS",None,"a desk calendar with several days crossed out, dim counter","top",[("narration","","그렇게 며칠이 지났다.")],"people"),
 ("wide","EXT",None,"another rainy night over the same neon storefront, low-detail empty area at top","top",[("narration","","매일 밤, 같은 시간.")],"people"),
 ("full","CVS","jiho","{j} now standing tense behind the counter, watching the clock intently, low-detail empty area at top-left","tl",[("thought","지호","오늘도… 올까.")],""),
 ("insert","CVS",None,"macro of the wall clock striking 3:00","br",[("sfx","","딸깍.")],"people"),
 ("wide","CVS",None,"the automatic door sliding open again, cold mist, the familiar pale silhouette","tr",[("sfx","","스르륵—")],"clear face"),
 ("full","CVS","yuna","{y} entering exactly as before, head lowered, silent","tr",[],""),
 ("emotion","CVS","jiho","{j} watching his own breath fog the cold air, eyes narrowing, low-detail empty area at top-left","tl",[("thought","지호","또 추워졌어… 에어컨도 안 켰는데.")],""),
 ("insert","CVS",None,"a small store thermometer dropping, faint frost forming, cold blue tone","top",[("narration","","그녀가 올 때마다 기온이 떨어졌다.")],"people"),
 ("full","CVS","yuna","{y} reaching toward the flower bucket, pale hand extended","tr",[],""),
 ("close","CVS","yuna","close on {y}'s pale cold hand lifting a white chrysanthemum, no warmth","bl",[],""),
 ("emotion","CVS","jiho","{j} suddenly glancing at the dark window behind her, puzzled, low-detail empty area at top-right","tr",[("thought","지호","어라…?")],""),
 ("insert","CVS",None,"the dark night window of the store acting as a mirror, reflecting the counter and shelves but the spot where a customer stands is empty, eerie","bottom",[("narration","","유리창에… 그녀만 비치지 않았다.")],"woman, person reflection"),
 ("emotion","CVS","jiho","{j} eyes widening in disbelief, rubbing his eyes, low-detail empty area at top-left","tl",[("thought","지호","잘못 봤겠지… 그래, 피곤해서.")],""),
 ("full","CVS","yuna","{y} placing the chrysanthemum on the counter, head lowered","bl",[("speech","손님","…이거 주세요.")],""),
 ("close","CVS","jiho","{j}'s hand trembling slightly as he scans the flower, low-detail empty area at top-left","tl",[("thought","지호","목소리가… 멀게 들려.")],""),
 ("full","CVS","yuna","{y} drifting out, the door sliding shut behind her","tr",[("sfx","","스르륵—")],""),
 ("wide","CVS",None,"the empty store floor where she walked, spotless, not a single wet footprint, eerie stillness, low-detail empty area at top","top",[("narration","","그녀가 지나간 자리엔, 발자국이 없었다.")],"people"),
 ("insert","CCTV",None,"a grainy CCTV monitor playback of the counter showing only the clerk, the spot in front of the counter conspicuously empty","bottom",[("narration","","CCTV에도, 그녀는 없었다.")],"woman, second person"),
 ("emotion","CCTV","jiho","{j} leaning close into the glowing CCTV monitor, cold dread on his face, low-detail empty area at top-left","tl",[("thought","지호","…뭐야 이거.")],""),
 ("close","CVS","jiho","{j} stepping back from the monitor, face pale and stiff, low-detail empty area at top-right","tr",[("speech","지호","말도 안 돼.")],""),
 ("insert","PHONE",None,"a smartphone screen with a news search bar, a partial search query typed, dim","top",[("narration","","그는 홀린 듯 검색했다.")],"people"),
 ("insert","PHONE",None,"a smartphone showing a scanned old newspaper article with a grainy photo of a young woman, the headline strip left as a low-detail blank band","top",[("narration","","「3개월 전 실종 여성, 인근 하천서 시신 발견」")],"readable text, people crowd"),
 ("emotion","CVS","jiho","{j} staring at the phone, recognition and horror dawning, low-detail empty area at top-left","tl",[("thought","지호","이 얼굴… 설마.")],""),
 ("insert","PHONE",None,"zoom into the grainy newspaper photograph, the face of a pale long-haired young woman becoming clear, ominous","bottom",[("narration","","사진 속 여자는, 매일 밤 오는 그 손님이었다.")],"readable text"),
 ("emotion","CVS","jiho","{j} dropping the phone, hand clamped over his mouth, eyes wide with horror, low-detail empty area at top-right","tr",[("speech","지호","헉…")],""),
 ("wide","CVS",None,"the lone clerk standing in the suddenly vast cold store, fluorescent lights buzzing, oppressive emptiness, low-detail empty area at top","top",[("narration","","그날 밤, 그는 잠들지 못했다.")],""),
 ("full","CVS","jiho","{j} the next night, gripping the counter edge, terrified, staring at the clock, low-detail empty area at top-left","tl",[("thought","지호","오지 마… 제발 오늘은 오지 마.")],""),
 ("insert","CVS",None,"macro of the clock hand crawling toward 3:00, heavy tension","br",[("sfx","","…똑… 딱…")],"people"),
 # ── ACT 3 · 반전·클라이맥스 (49-70) ───────────────────
 ("insert","CVS",None,"macro of the clock striking exactly 3:00","br",[("sfx","","딸깍.")],"people"),
 ("wide","CVS",None,"the automatic door staying shut, total silence, no mist, the store unnervingly still, low-detail empty area at top","top",[("narration","","그런데, 문이 열리지 않았다.")],"people"),
 ("emotion","CVS","jiho","{j} looking confused, a sliver of fragile relief on his face, low-detail empty area at top-right","tr",[("thought","지호","…안 와?")],""),
 ("close","CVS","jiho","{j} stiffening as a cold breath touches the back of his neck, hair rising, low-detail empty area at top-left","tl",[("sfx","","후—")],""),
 ("emotion","CVS","jiho","{j} frozen, eyes wide, slowly realizing something is right behind him, low-detail empty area at top-left","tl",[("thought","지호","…뒤에.")],""),
 ("wide","CVS","yuna","{y} standing silently right behind the counter beside the frozen clerk, head lowered, the clerk seen from behind","tr",[],""),
 ("emotion","CVS","jiho","{j} slowly turning his head, face contorted with terror, low-detail empty area at top-right","tr",[("speech","지호","어떻게…")],""),
 ("full","CVS","yuna","{y} slowly raising her head for the very first time","tr",[],""),
 ("emotion","CVS","yuna","extreme close-up of {y}'s face fully revealed at last, pale skin, hollow sorrowful eyes, a faint sad smile","bl",[],""),
 ("emotion","CVS","jiho","{j}'s frozen face, tears of fear welling, low-detail empty area at top-left","tl",[("thought","지호","신문 속… 그 여자.")],""),
 ("close","CVS","yuna","{y} speaking softly, gentle and sorrowful expression","bl",[("speech","손님","놀라게 해서… 미안해요.")],""),
 ("emotion","CVS","jiho","{j} trembling, unable to speak, low-detail empty area at top-right","tr",[("thought","지호","…")],""),
 ("close","CVS","yuna","{y} with a lonely sad gaze, faint smile","bl",[("speech","손님","다들 절 못 봐요. 그냥… 지나쳐요.")],""),
 ("close","CVS","yuna","{y} eyes glistening, a faint heartbreaking smile","bl",[("speech","손님","그런데 당신은… 절 봐줬어요.")],""),
 ("emotion","CVS","jiho","{j}, fear melting into pity, conflicted, low-detail empty area at top-left","tl",[("thought","지호","…왜, 왜 나한테.")],""),
 ("full","CVS","yuna","{y} holding out the white chrysanthemum toward the clerk with both hands","tr",[("speech","손님","이 꽃… 우리 엄마한테 전해줄래요?")],""),
 ("insert","CVS",None,"the white chrysanthemum resting on the counter, a thin layer of frost on its petals, ice-cold","bottom",[("narration","","꽃은… 얼음처럼 차가웠다.")],"people"),
 ("emotion","CVS","jiho","{j} looking down at the flower then back at her, torn between fear and sorrow, low-detail empty area at top-right","tr",[],""),
 ("close","CVS","yuna","{y} with a faint, grateful, heartbreaking smile, a tear sliding down","bl",[("speech","손님","드디어… 절 봐주는 사람이 생겼네요.")],""),
 ("wide","CVS",None,"the fluorescent ceiling lights flickering violently, the store strobing into shadow, low-detail empty area at top","top",[("sfx","","지직— 직—")],"people"),
 ("wide","CVS",None,"the lights gone out, the store in darkness lit only by outside neon, the woman vanished, only the chrysanthemum left on the counter, low-detail empty area at top","top",[("narration","","불이 들어왔을 때, 그녀는 없었다.")],"people, woman"),
 ("full","CVS","jiho","{j} alone in the dim store, clutching the frozen white flower, staring at the silent door with dread and sorrow, low-detail empty area at top","top",[("narration","","그리고 그 꽃은, 아직 내 손에 있다."),("narration","","다음 손님은… 누구일까.")],""),
]

def ipfor(shot):
    if shot in ("full","wide"): return ("full",0.4)
    if shot in ("close","emotion"): return ("face",0.5)
    return (None,None)

def descfor(char):
    return {"j":JIHO_DESC,"y":YUNA_DESC}

jobs=[]; lettering={}
for i,(shot,loc,char,scene,bspace,lines,negx) in enumerate(B,1):
    pid=f"panel_{i:03d}"
    scene=scene.format(j=JIHO_DESC,y=YUNA_DESC)
    prompt=f"anime illustration style, {SHOT[shot]}{scene}, {LOC[loc]}{QUAL}"
    neg=NEG+((", "+negx) if negx else "")
    job={"output":f"{pid}.png","scene_group":("A" if i<=20 else "B" if i<=48 else "C"),
         "shot":shot,"panel_id":pid,"prompt":prompt,"model":"animagine","style":"illustration",
         "negative_prompt":neg,"width":896,"height":1280,"seed":2000+i,"steps":30,"cfg":6.5}
    mode,strength=ipfor(shot)
    if char and mode:
        job["character_ids"]=[char]
        job["character_id"]=JIHO if char=="jiho" else YUNA
        job["ip_adapter_mode"]=mode; job["ip_adapter_strength"]=strength
    jobs.append(job)
    # lettering
    top,left,tail,mw=BS[bspace]
    bl=[]
    for (typ,spk,txt) in lines:
        bl.append([typ,spk,txt,top,left,tail,mw])
        # 두 번째 줄은 아래로 내려 겹침 방지
        if len(lines)>1:
            top=f"{int(top.rstrip('%'))+ (10 if typ=='narration' else 14)}%"
    lettering[f"{pid}.png"]=bl

here=os.path.dirname(os.path.abspath(__file__))
json.dump(jobs,open(os.path.join(here,"ep01full_jobs.json"),"w"),ensure_ascii=False,indent=1)
json.dump(lettering,open(os.path.join(here,"ep01full_lettering.json"),"w"),ensure_ascii=False,indent=1)
nchar=sum(1 for j in jobs if "character_id" in j)
print(f"jobs={len(jobs)}  with character_id={nchar}  no-bubble-word={'OK' if all('speech bubble' not in j['prompt'] for j in jobs) else 'FAIL'}")
print("acts:",sum(j['scene_group']=='A' for j in jobs),sum(j['scene_group']=='B' for j in jobs),sum(j['scene_group']=='C' for j in jobs))
