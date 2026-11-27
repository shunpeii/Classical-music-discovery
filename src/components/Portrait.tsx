import {useState} from 'react';
import type {Composer} from '../types';
const images:Record<string,string>={beethoven:'Beethoven.jpg',mozart:'Wolfgang-amadeus-mozart_1.jpg',bach:'Johann Sebastian Bach.jpg',haydn:'Joseph Haydn.jpg',chopin:'Frederic Chopin photo.jpeg',schubert:'Franz Schubert by Wilhelm August Rieder 1875.jpg',mendelssohn:'Felix Mendelssohn Bartholdy.jpg'};
export function Portrait({composer}:{composer:Composer}){const [failed,setFailed]=useState(false);const file=images[composer.id];return <div className="composer-photo">{file&&!failed?<img src={'https://commons.wikimedia.org/wiki/Special:FilePath/'+encodeURIComponent(file)+'?width=360'} alt={composer.name} onError={()=>setFailed(true)}/>:<span>{composer.name.slice(0,1)}</span>}</div>}
