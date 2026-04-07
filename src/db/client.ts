import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
dotenv.config();

export const db = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export type BusinessStatus =
  | 'discovered'
  | 'site_built'
  | 'email_found'
  | 'email_sent'
  | 'replied'
  | 'interested'
  | 'sold'
  | 'delivered'
  | 'declined'
  | 'unsubscribed';

export interface Business {
  id?: string;
  place_id: string;
  name: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  phone?: string;
  email?: string;
  website?: string;
  category?: string;
  industry?: string;
  hours?: string[];
  photos?: string[];
  rating?: number;
  review_count?: number;
  reviews?: string[];
  lat?: number;
  lng?: number;
  needs_scheduling?: boolean;
  status?: BusinessStatus;
}
