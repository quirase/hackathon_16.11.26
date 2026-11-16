import type { CefrLevel } from '../types/analysis';

export interface CefrMeta {
  level: CefrLevel;
  index: number;
  name: string;
  shortDesc: string;
  fg: string;
  bg: string;
  border: string;
}

export const CEFR_ORDER: CefrLevel[] = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export const CEFR_META: Record<CefrLevel, CefrMeta> = {
  A1: {
    level: 'A1',
    index: 0,
    name: 'Beginner',
    shortDesc: 'Everyday expressions & slow, clear speech',
    fg: '#17655B',
    bg: '#E6F4F1',
    border: '#A7D7CE',
  },
  A2: {
    level: 'A2',
    index: 1,
    name: 'Elementary',
    shortDesc: 'Routine topics, simple sentences & high-frequency words',
    fg: '#1E4FD6',
    bg: '#EBF2FF',
    border: '#B8CEF9',
  },
  B1: {
    level: 'B1',
    index: 2,
    name: 'Intermediate',
    shortDesc: 'Clear standard speech on familiar subjects',
    fg: '#9A4A06',
    bg: '#FEF3D6',
    border: '#F2CE84',
  },
  B2: {
    level: 'B2',
    index: 3,
    name: 'Upper-Intermediate',
    shortDesc: 'Abstract ideas, natural pace & idiomatic phrasing',
    fg: '#B93815',
    bg: '#FFEDE6',
    border: '#F5BCA8',
  },
  C1: {
    level: 'C1',
    index: 4,
    name: 'Advanced',
    shortDesc: 'Nuanced argument, dense vocabulary & rapid delivery',
    fg: '#93183A',
    bg: '#FFE5EC',
    border: '#EEB2C2',
  },
  C2: {
    level: 'C2',
    index: 5,
    name: 'Mastery',
    shortDesc: 'Specialized register, subtle irony & native-speed idiomaticity',
    fg: '#4C1D95',
    bg: '#EFEAFE',
    border: '#C8B8F8',
  },
};

export function isCefrAtLeast(level: CefrLevel, minLevel: CefrLevel): boolean {
  return CEFR_META[level].index >= CEFR_META[minLevel].index;
}
