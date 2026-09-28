import os, requests
from datetime import datetime, timezone

TOKEN=os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID=os.environ["TELEGRAM_CHAT_ID"]
SYMBOL=os.getenv("SYMBOL","PHAUSDT")

def klines(interval,limit=250):
    r=requests.get("https://fapi.binance.com/fapi/v1/klines",
                   params={"symbol":SYMBOL,"interval":interval,"limit":limit},timeout=30)
    r.raise_for_status()
    return r.json()

def ema(v,n):
    e=sum(v[:n])/n; k=2/(n+1)
    for x in v[n:]: e=x*k+e*(1-k)
    return e

def rsi(v,n=14):
    d=[v[i]-v[i-1] for i in range(1,len(v))]
    g=[max(x,0) for x in d]; l=[max(-x,0) for x in d]
    ag=sum(g[:n])/n; al=sum(l[:n])/n
    for i in range(n,len(d)):
        ag=(ag*(n-1)+g[i])/n; al=(al*(n-1)+l[i])/n
    return 100 if al==0 else 100-100/(1+ag/al)

def analyze(tf):
    d=klines(tf); c=[float(x[4]) for x in d]; h=[float(x[2]) for x in d]; l=[float(x[3]) for x in d]
    e20,e50,e200=ema(c,20),ema(c,50),ema(c,200)
    rs=rsi(c)
    mac=[]
    for i in range(26,len(c)+1):
        q=c[:i]; mac.append(ema(q,12)-ema(q,26))
    m=mac[-1]; sig=ema(mac,9) if len(mac)>=9 else m
    bull=sum([c[-1]>e20,e20>e50,e50>e200,rs>=50,m>sig])
    trend="BULLISH" if bull>=4 else "BEARISH" if bull<=1 else "NEUTRAL"
    return dict(price=c[-1],ema20=e20,ema50=e50,ema200=e200,rsi=rs,macd=m,signal=sig,
                support=min(l[-50:]),resistance=max(h[-50:]),trend=trend)

def f(x):
    return f"{x:.4f}" if x>=1 else f"{x:.7f}"

def report():
    a15,a1,a4=map(analyze,("15m","1h","4h")); p=a15["price"]
    bulls=sum(x["trend"]=="BULLISH" for x in (a15,a1,a4))
    bears=sum(x["trend"]=="BEARISH" for x in (a15,a1,a4))
    if bulls>=2:
        bias="LONG BIAS"; sl=min(a15["support"],a1["support"])*.995
        risk=max(p-sl,p*.005); entry=f"{f(min(a15['support'],a1['support']))} - {f(p)}"
        levels=[f"Entry: {entry}",f"SL: {f(sl)}",f"TP1: {f(p+risk*1.5)}",f"TP2: {f(p+risk*2.5)}"]
    elif bears>=2:
        bias="SHORT BIAS"; sl=max(a15["resistance"],a1["resistance"])*1.005
        risk=max(sl-p,p*.005); entry=f"{f(p)} - {f(max(a15['resistance'],a1['resistance']))}"
        levels=[f"Entry: {entry}",f"SL: {f(sl)}",f"TP1: {f(p-risk*1.5)}",f"TP2: {f(p-risk*2.5)}"]
    else:
        bias="NO TRADE / WAIT"; levels=["Wait for clearer confirmation."]
    return "\n".join([
        "📊 PHA/USDT FUTURES DAILY ANALYSIS",
        datetime.now(timezone.utc).strftime("🕒 %Y-%m-%d %H:%M UTC"),
        f"💰 Price: {f(p)}","",
        "📈 TRENDS",
        f"15M: {a15['trend']} | RSI {a15['rsi']:.1f}",
        f"1H: {a1['trend']} | RSI {a1['rsi']:.1f}",
        f"4H: {a4['trend']} | RSI {a4['rsi']:.1f}","",
        f"🎯 BIAS: {bias}","",
        "📍 LEVELS",
        f"15M Support: {f(a15['support'])}",
        f"1H Support: {f(a1['support'])}",
        f"15M Resistance: {f(a15['resistance'])}",
        f"1H Resistance: {f(a1['resistance'])}","",
        "📐 1H INDICATORS",
        f"EMA20: {f(a1['ema20'])}",
        f"EMA50: {f(a1['ema50'])}",
        f"EMA200: {f(a1['ema200'])}",
        f"MACD: {a1['macd']:.8f} | Signal: {a1['signal']:.8f}","",
        "🧭 TRADE PLAN (ANALYSIS ONLY)",*levels,"",
        "⚠️ No automatic orders. Verify levels and use risk management."
    ])

if __name__=="__main__":
    r=requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    json={"chat_id":CHAT_ID,"text":report()},timeout=30)
    r.raise_for_status()
