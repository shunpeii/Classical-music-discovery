import type {ReactNode} from 'react';
import type {Era,Composer,Work,Concert} from '../types';
type Props={work:Work;go:(r:string)=>void;spotify:(w:Work)=>string;cards:(items:Concert[])=>ReactNode;concerts:Concert[];id:string};
export function WorkPage({work,go,spotify,cards,concerts,id}:Props){return <><button onClick={()=>go('composer/'+work.composerId)}>← 作曲家</button><h1>{work.title}</h1><a href={spotify(work)} target="_blank" rel="noreferrer">▷ Spotifyで聴く</a><section className="listen-note"><small>LISTENING GUIDE</small><h2>聴きどころ</h2><p>{work.guide||"解説は準備中です。"}</p></section><h2>この曲を生で聴く</h2>{cards(concerts.filter(c=>c.workIds.includes(id)))}</>;}
