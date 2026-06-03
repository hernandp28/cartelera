export interface TeamRef {
  id: number | string;
  name: string;
  code?: string | null;
  flag_url?: string | null;
  logo_url?: string | null;
}

export interface MatchEvent {
  minute?: number | null;
  player: string;
  team_side: "home" | "away";
}

export interface MatchCard {
  id: number | string;
  date: string;
  kickoff: string;
  status: string;
  minute?: number | null;
  stage?: string | null;
  group?: string | null;
  venue?: string | null;
  home: TeamRef;
  away: TeamRef;
  home_score?: number | null;
  away_score?: number | null;
  home_pens?: number | null;
  away_pens?: number | null;
  scorers: MatchEvent[];
  red_cards: MatchEvent[];
}

export interface GroupRow {
  position: number;
  team: TeamRef;
  points: number;
  played: number;
  goal_diff: number;
}

export interface GroupTable {
  group: string;
  rows: GroupRow[];
}

export interface UpcomingMatch {
  kickoff: string;
  home: string;
  away: string;
}

export interface LineupPlayer {
  name: string | null;
  number: number | null;
  pos: string | null;
}

export interface TeamLineup {
  team: TeamRef;
  coach: string | null;
  formation: string | null;
  startXI: LineupPlayer[];
  substitutes: LineupPlayer[];
}

export interface LineupsResponse {
  home: TeamLineup | null;
  away: TeamLineup | null;
}

export interface CarteleraResponse {
  date: string;
  timezone: string;
  source: string;
  is_demo: boolean;
  title: string;
  agenda: MatchCard[];
  groups: GroupTable[];
  tomorrow: UpcomingMatch[];
  generated_at: string;
}
