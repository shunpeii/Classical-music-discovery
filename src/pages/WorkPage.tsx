import type {ReactNode} from 'react';
import type {Era,Composer,Work,Concert} from '../types';
type Props={work:Work;go:(r:string)=>void;spotify:(w:Work)=>string;cards:(items:Concert[])=>ReactNode;concerts:Concert[];id:string};
export function WorkPage({work,go,spotify,cards,concerts,id}:Props){return <><section className="work-hero"><button className="back" onClick={()=>go('composer/'+work.composerId)}>←</button><span className="music-mark">♫</span><h1>{work.title}</h1></section><div className="detail-body"><p>{work.guide||'解説は準備中です。'}</p><a className="listen-button" href={spotify(work)} target="_blank" rel="noreferrer">▶ Spotifyでこの曲を聴く</a><h2>この曲が聴けるコンサート</h2><p>{concerts.filter(c=>c.workIds.includes(id)).length}件の公演</p>{cards(concerts.filter(c=>c.workIds.includes(id)))}</div></>;}
