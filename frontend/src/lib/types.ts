/** Mirrors the API's response models. Money is a string with its currency —
 *  never a number, so nothing becomes a float on the way here. */

export type Money = {
  amount: string;
  currency: string;
};

export type BandPosition = "below" | "within" | "above";

export type PayReason =
  | "hire"
  | "merit"
  | "promotion"
  | "market_adjustment"
  | "correction";

export type PayEntry = {
  effective_from: string;
  amount: Money;
  base_amount: Money;
  reason: PayReason;
  note: string | null;
};

export type EmployeeSummary = {
  id: number;
  staff_number: string;
  name: string;
  email: string;
  country: string;
  location: string;
  department: string;
  job_family: string;
  level: string;
  hired_on: string;
  left_on: string | null;
  pay: Money | null;
  base_pay: Money | null;
  pay_effective_from: string | null;
  compa_ratio: string | null;
  band_position: BandPosition | null;
};

export type Band = {
  low: Money;
  mid: Money;
  high: Money;
};

export type EmployeeDetail = EmployeeSummary & {
  band: Band | null;
  history: PayEntry[];
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type Spread = {
  lowest: Money;
  p25: Money;
  median: Money;
  p75: Money;
  highest: Money;
};

export type BandCounts = {
  below: number;
  within: number;
  above: number;
};

export type GroupStats = {
  key: string;
  label: string;
  headcount: number;
  pay: Spread;
  compa_median: string;
  band: BandCounts;
};

export type Distribution = {
  dimension: string;
  as_of: string;
  basis: "base" | "local";
  groups: GroupStats[];
};

export type Overview = {
  headcount: number;
  payroll: Money;
  pay: Spread;
  compa_median: string;
  band: BandCounts;
  as_of: string;
  unmeasured: number;
};

export type PayChangeResult = {
  employee_id: number;
  entry: PayEntry;
  compa_ratio: string | null;
  band_position: BandPosition | null;
  in_effect: boolean;
};

export type CountryRef = {
  code: string;
  name: string;
  currency: string;
};

export type LevelRef = {
  code: string;
  rank: number;
};

export type Reference = {
  countries: CountryRef[];
  departments: string[];
  families: string[];
  levels: LevelRef[];
};

export const SORTS = ["name", "salary", "level", "hired", "compa"] as const;
export type Sort = (typeof SORTS)[number];

export const DIMENSIONS = [
  "country",
  "department",
  "family",
  "level",
] as const;
export type Dimension = (typeof DIMENSIONS)[number];

export const REASONS: { value: PayReason; label: string }[] = [
  { value: "merit", label: "Merit increase" },
  { value: "promotion", label: "Promotion" },
  { value: "market_adjustment", label: "Market adjustment" },
  { value: "correction", label: "Correction" },
  { value: "hire", label: "Starting salary" },
];
