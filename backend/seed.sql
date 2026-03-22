-- Script de seed pour FoodTracker
-- Crée un utilisateur admin par défaut
-- Mot de passe : "secret" hashé en bcrypt (à changer !)

INSERT INTO users (id, username, email, hashed_password, is_admin)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'admin',
  'admin@foodtracker.local',
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
  true
)
ON CONFLICT (id) DO NOTHING;
