export type Sample = {
  t: string;
  lat: number | null;
  lon: number | null;
  alt_m?: number | null;
  speed_mps: number | null;
  heading_deg?: number | null;
  num_sats?: number | null;
  hdop?: number | null;
  vdop?: number | null;
  pdop?: number | null;
  cn0_mean_dbhz?: number | null;
  cn0_min_dbhz?: number | null;
  cn0_max_dbhz?: number | null;
  anomaly_flags?: string[];
};

export type AnalyzeResponse = {
  spoofing_score?: number | null;
  meta: any;
  summary: any;
  track: { samples: Sample[] };
};
