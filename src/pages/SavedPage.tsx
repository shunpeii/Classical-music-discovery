import type {ReactNode} from 'react';
import type {Concert} from '../types';
type Props={cards:(items:Concert[])=>ReactNode;concerts:Concert[];saved:string[]};
export function SavedPage({cards,concerts,saved}:Props){return <><h1>お気に入り</h1>{cards(concerts.filter(c=>saved.includes(c.id)))}</>;}
