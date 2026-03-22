-- ============================================================
-- Données de test — produits + stock avec DLC variées
-- Toutes les dates sont relatives à CURRENT_DATE
-- À exécuter après seed.sql
-- ============================================================

-- ── Produits ─────────────────────────────────────────────────

INSERT INTO products (barcode, name, brand, category, nutriscore, energy_kcal, proteins_g, carbs_g, fat_g)
VALUES
  ('3033710065967', 'Yaourt Nature',            'Danone',     'Produits laitiers',  'A', 56,  4.3, 6.1, 1.4),
  ('3228881010481', 'Lait Demi-Écrémé 1L',      'Lactel',     'Produits laitiers',  'B', 46,  3.2, 4.8, 1.5),
  ('3073781011684', 'Camembert de Normandie',   'Président',  'Fromages',           'D', 300, 20.0, 0.5, 24.5),
  ('8076802085738', 'Pâtes Complètes 500g',     'Barilla',    'Féculents',          'B', 357, 13.0, 70.0, 2.0),
  ('5010477348578', 'Riz Basmati 1kg',          'Uncle Ben''s','Féculents',          'B', 350, 7.5,  77.0, 0.9),
  ('3155250352006', 'Huile d''Olive Vierge',    'Puget',      'Huiles et graisses', 'C', 824, 0.0,  0.0, 91.6),
  ('3038350260233', 'Soupe Légumes Moulinée',   'Knorr',      'Soupes',             'B', 35,  1.1,  6.0, 0.5),
  ('3414970085132', 'Jus d''Orange Pressée',    'Tropicana',  'Boissons',           'C', 43,  0.7, 10.0, 0.1),
  ('7613035349094', 'Muesli Croustillant',      'Nestlé',     'Céréales',           'C', 402, 8.0, 68.0, 10.0),
  ('3017620429484', 'Nutella 400g',             'Ferrero',    'Pâtes à tartiner',   'E', 539, 6.3, 57.5, 30.9)
ON CONFLICT (barcode) DO NOTHING;


-- ── Stock items ───────────────────────────────────────────────
-- Scénarios couverts :
--   • Expiré         (DLC dépassée)
--   • Urgent J-1     (expire demain)
--   • Urgent J-2     (expire dans 2 jours)
--   • Bientôt J-5    (expire dans 5 jours)
--   • OK J-14        (expire dans 2 semaines)
--   • OK J-45        (expire dans 6 semaines)
--   • Sans DLC       (produits secs)

INSERT INTO stock_items (id, household_id, product_barcode, quantity, unit, location, opened)
VALUES
  -- Expiré : camembert entamé au frigo
  ('aaaaaaaa-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000001',
   '3073781011684', 0.5, 'unité', 'Frigo', true),

  -- Urgent J-1 : yaourt presque fini
  ('aaaaaaaa-0000-0000-0000-000000000002',
   '00000000-0000-0000-0000-000000000001',
   '3033710065967', 2, 'unité', 'Frigo', false),

  -- Urgent J-2 : lait ouvert
  ('aaaaaaaa-0000-0000-0000-000000000003',
   '00000000-0000-0000-0000-000000000001',
   '3228881010481', 0.7, 'L', 'Frigo', true),

  -- Bientôt J-5 : jus d'orange
  ('aaaaaaaa-0000-0000-0000-000000000004',
   '00000000-0000-0000-0000-000000000001',
   '3414970085132', 1, 'unité', 'Frigo', false),

  -- OK J-14 : soupe congelée
  ('aaaaaaaa-0000-0000-0000-000000000005',
   '00000000-0000-0000-0000-000000000001',
   '3038350260233', 3, 'unité', 'Congélateur', false),

  -- OK J-45 : yaourt en réserve
  ('aaaaaaaa-0000-0000-0000-000000000006',
   '00000000-0000-0000-0000-000000000001',
   '3033710065967', 6, 'unité', 'Frigo', false),

  -- Sans DLC : pâtes
  ('aaaaaaaa-0000-0000-0000-000000000007',
   '00000000-0000-0000-0000-000000000001',
   '8076802085738', 2, 'unité', 'Placard', false),

  -- Sans DLC : riz
  ('aaaaaaaa-0000-0000-0000-000000000008',
   '00000000-0000-0000-0000-000000000001',
   '5010477348578', 1, 'kg', 'Placard', false),

  -- Sans DLC : huile d'olive
  ('aaaaaaaa-0000-0000-0000-000000000009',
   '00000000-0000-0000-0000-000000000001',
   '3155250352006', 750, 'ml', 'Placard', false),

  -- Sans DLC : nutella ouvert
  ('aaaaaaaa-0000-0000-0000-000000000010',
   '00000000-0000-0000-0000-000000000001',
   '3017620429484', 1, 'unité', 'Placard', true),

  -- Sans DLC : muesli
  ('aaaaaaaa-0000-0000-0000-000000000011',
   '00000000-0000-0000-0000-000000000001',
   '7613035349094', 500, 'g', 'Placard', true)

ON CONFLICT (id) DO NOTHING;


-- ── Dates de péremption ───────────────────────────────────────

INSERT INTO expiry_dates (id, stock_item_id, expiry_date, alert_days_before, alerted)
VALUES
  -- Expiré (il y a 5 jours)
  ('bbbbbbbb-0000-0000-0000-000000000001',
   'aaaaaaaa-0000-0000-0000-000000000001',
   CURRENT_DATE - INTERVAL '5 days', 3, true),

  -- Urgent J-1
  ('bbbbbbbb-0000-0000-0000-000000000002',
   'aaaaaaaa-0000-0000-0000-000000000002',
   CURRENT_DATE + INTERVAL '1 day', 3, false),

  -- Urgent J-2
  ('bbbbbbbb-0000-0000-0000-000000000003',
   'aaaaaaaa-0000-0000-0000-000000000003',
   CURRENT_DATE + INTERVAL '2 days', 3, false),

  -- Bientôt J-5
  ('bbbbbbbb-0000-0000-0000-000000000004',
   'aaaaaaaa-0000-0000-0000-000000000004',
   CURRENT_DATE + INTERVAL '5 days', 3, false),

  -- OK J-14
  ('bbbbbbbb-0000-0000-0000-000000000005',
   'aaaaaaaa-0000-0000-0000-000000000005',
   CURRENT_DATE + INTERVAL '14 days', 7, false),

  -- OK J-45
  ('bbbbbbbb-0000-0000-0000-000000000006',
   'aaaaaaaa-0000-0000-0000-000000000006',
   CURRENT_DATE + INTERVAL '45 days', 7, false)

ON CONFLICT (id) DO NOTHING;
