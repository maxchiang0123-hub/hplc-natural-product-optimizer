"""Agilent-compatible (CSV export) HPLC natural-product method explorer.
Research decision support only: no instrument control or validated predictions.
Run: streamlit run app.py
"""
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy.signal import find_peaks, peak_widths, savgol_filter

st.set_page_config(page_title='HPLC Natural Product Optimizer', layout='wide')
st.title('HPLC Natural Product Method Explorer')
st.caption('Agilent-compatible via exported CSV; offline research decision support. No instrument control.')

@st.cache_data
def demo_data():
    t=np.linspace(0,35,3501)
    y=0.015+0.0015*t
    for mu,sigma,height in [(6.5,.23,.4),(11.8,.34,.7),(14.0,.30,.9),(14.7,.32,.7),(21.3,.45,1.0),(27.0,.5,.45)]:
        y+=height*np.exp(-0.5*((t-mu)/sigma)**2)
    rng=np.random.default_rng(42)
    return pd.DataFrame({'Time (min)':t,'Signal (mAU)':y+rng.normal(0,.008,len(t))})

def read_csv(upload):
    raw=upload.getvalue()
    for encoding in ('utf-8-sig','utf-16','latin1'):
        try:
            df=pd.read_csv(io.BytesIO(raw),encoding=encoding,sep=None,engine='python',comment='#')
            if df.shape[1]>=2:return df
        except Exception:pass
    raise ValueError('Could not read CSV. Export a two-column time/signal CSV from Agilent OpenLab/ChemStation.')

def analyze(t,y,smooth_window,prominence,min_distance):
    order=np.argsort(t);t=np.asarray(t,dtype=float)[order];y=np.asarray(y,dtype=float)[order]
    valid=np.isfinite(t)&np.isfinite(y);t=t[valid];y=y[valid]
    if len(t)<15 or np.any(np.diff(t)<=0):raise ValueError('Need at least 15 unique, increasing time values.')
    n=min(smooth_window,len(y) if len(y)%2 else len(y)-1)
    if n<5:n=5
    smooth=savgol_filter(y,n,2)
    # Approximate baseline via a low quantile of the signal (not a validated integration baseline).
    baseline=np.quantile(smooth,.05)
    corrected=smooth-baseline
    dt=float(np.median(np.diff(t)))
    distance=max(1,int(min_distance/dt))
    indices,properties=find_peaks(corrected,prominence=prominence,distance=distance)
    widths,_,left,right=peak_widths(corrected,indices,rel_height=.5)
    rows=[]
    for i,idx in enumerate(indices):
        left_t=np.interp(left[i],np.arange(len(t)),t)
        right_t=np.interp(right[i],np.arange(len(t)),t)
        rows.append({'Peak':i+1,'tR (min)':float(t[idx]),'Height':float(corrected[idx]),'FWHM (min)':float(right_t-left_t)})
    result=pd.DataFrame(rows)
    if len(result)>1:
        rs=[]
        for i in range(len(result)-1):
            a,b=result.iloc[i],result.iloc[i+1]
            # Gaussian approximation: baseline width ~1.699 * FWHM.
            rs.append(2*(b['tR (min)']-a['tR (min)'])/(1.699*(a['FWHM (min)']+b['FWHM (min)'])))
        result['Rs to next (approx.)']=rs+[np.nan]
    else:result['Rs to next (approx.)']=np.nan
    return t,y,smooth,result

st.sidebar.header('Method settings')
start_b=st.sidebar.number_input('Starting %B',0.,100.,10.,1.)
end_b=st.sidebar.number_input('Ending %B',0.,100.,90.,1.)
gradient_start=st.sidebar.number_input('Gradient start (min)',0.,1000.,2.,.5)
gradient_end=st.sidebar.number_input('Gradient end (min)',0.,1000.,30.,.5)
flow=st.sidebar.number_input('Flow (mL/min)',0.001,100.,1.,.1)
column=st.sidebar.text_input('Column / stationary phase','C18 (enter actual column)')
st.sidebar.info('Use measured conditions from your own method. Suggestions are hypotheses requiring experimental validation.')

uploaded=st.file_uploader('Upload Agilent-exported chromatogram CSV (time and detector signal)',type=['csv','txt'])
if uploaded is None:
    st.info('Showing reproducible synthetic demonstration data. Upload your own Agilent CSV to analyze a real run.')
    df=demo_data()
else:
    try:df=read_csv(uploaded)
    except Exception as e:st.error(str(e));st.stop()
cols=list(df.columns)
c1,c2=st.columns(2)
with c1:time_col=st.selectbox('Time column',cols,index=0)
with c2:signal_col=st.selectbox('Signal column',cols,index=min(1,len(cols)-1))
settings=st.expander('Peak detection settings',expanded=False)
with settings:
    smooth_window=st.slider('Savitzky–Golay smoothing window (samples)',5,151,31,2)
    prominence=st.number_input('Minimum peak prominence (signal units)',0.,1e9,.07,.01)
    min_distance=st.number_input('Minimum peak spacing (min)',0.01,100.,.3,.1)
try:
    t,y,smooth,peaks=analyze(pd.to_numeric(df[time_col],errors='coerce'),pd.to_numeric(df[signal_col],errors='coerce'),smooth_window,prominence,min_distance)
except Exception as e:st.error(f'Analysis error: {e}');st.stop()
fig,ax=plt.subplots(figsize=(11,4));ax.plot(t,y,alpha=.4,label='Raw signal');ax.plot(t,smooth,label='Smoothed')
for _,r in peaks.iterrows():ax.axvline(r['tR (min)'],alpha=.25,color='gray');ax.annotate(str(int(r['Peak'])),(r['tR (min)'],r['Height']+np.quantile(smooth,.05)),fontsize=8)
ax.set(xlabel='Retention time (min)',ylabel='Detector response',title='Chromatogram and detected peaks');ax.legend();st.pyplot(fig)
st.subheader('Detected peaks')
st.dataframe(peaks.style.format({'tR (min)':'{:.2f}','Height':'{:.3f}','FWHM (min)':'{:.3f}','Rs to next (approx.)':'{:.2f}'}) if len(peaks) else peaks,use_container_width=True)
st.download_button('Download peak table (CSV)',peaks.to_csv(index=False).encode(),'hplc_peaks.csv','text/csv')

st.subheader('Separation assessment and next-run suggestions')
if gradient_end<=gradient_start or end_b<=start_b:
    st.warning('For this prototype, enter an increasing linear gradient with end time after start time and ending %B greater than starting %B.')
elif len(peaks)<2:
    st.warning('Fewer than two peaks detected; adjust peak detection or upload a chromatogram with measurable peaks.')
else:
    pairs=peaks.iloc[:-1].copy()
    critical=pairs.loc[pairs['Rs to next (approx.)'].idxmin()]
    i=int(critical['Peak'])-1
    next_peak=peaks.iloc[i+1]
    midpoint=(critical['tR (min)']+next_peak['tR (min)'])/2
    def b_at(tm):return start_b+(end_b-start_b)*np.clip((tm-gradient_start)/(gradient_end-gradient_start),0,1)
    mid_b=float(b_at(midpoint));slope=(end_b-start_b)/(gradient_end-gradient_start)
    rs=float(critical['Rs to next (approx.)'])
    st.metric('Critical adjacent-pair resolution (approx.)',f'{rs:.2f}')
    st.write(f"Critical pair: peaks **{i+1} and {i+2}**, at **{critical['tR (min)']:.2f}** and **{next_peak['tR (min)']:.2f} min**. Estimated elution strength near pair: **{mid_b:.1f}% B**.")
    if rs<1.5:st.warning('Approximate Rs < 1.5: possible overlap. Confirm using validated integration and compound identity data.')
    else:st.success('All detected adjacent pairs meet approximate Rs ≥ 1.5; confirm purity and identity independently.')
    st.markdown('**Candidate experiments (not predictions)**')
    # Keep the same B range but decrease gradient slope, to explore selectivity around critical pair.
    candidates=pd.DataFrame([
        {'Experiment':'Current reference','Start %B':start_b,'End %B':end_b,'Gradient start (min)':gradient_start,'Gradient end (min)':gradient_end,'Slope (%B/min)':slope,'Rationale':'Measured reference'},
        {'Experiment':'Shallower full gradient','Start %B':start_b,'End %B':end_b,'Gradient start (min)':gradient_start,'Gradient end (min)':gradient_start+1.5*(gradient_end-gradient_start),'Slope (%B/min)':slope/1.5,'Rationale':'Test whether a lower gradient slope improves separation'},
        {'Experiment':'Focused window around critical pair','Start %B':max(0,mid_b-12),'End %B':min(100,mid_b+12),'Gradient start (min)':gradient_start,'Gradient end (min)':gradient_end,'Slope (%B/min)':(min(100,mid_b+12)-max(0,mid_b-12))/(gradient_end-gradient_start),'Rationale':'Screen a narrower solvent-strength range; may lose other peaks'},
    ])
    st.dataframe(candidates.style.format({'Start %B':'{:.1f}','End %B':'{:.1f}','Gradient start (min)':'{:.1f}','Gradient end (min)':'{:.1f}','Slope (%B/min)':'{:.2f}'}),use_container_width=True)
    st.download_button('Download candidate methods (CSV)',candidates.to_csv(index=False).encode(),'candidate_methods.csv','text/csv')
    st.write('**Suggested experiment:** Run one candidate at a time with the same column, temperature, mobile-phase chemistry, detector, and injection load. Re-import each chromatogram and compare critical-pair resolution, retention, and runtime. These are heuristic screening suggestions, not a retention-model fit.')

st.caption('Limitations: assumes approximately uniform sampling and near-Gaussian peaks; uses FWHM-based resolution, not validated baseline widths. No peak identity, fraction-collection commands, preparative loading, safety limits, or Agilent .D parsing. Verify solvent compatibility, pressure limits, sample stability, and lab SOPs before running methods.')
