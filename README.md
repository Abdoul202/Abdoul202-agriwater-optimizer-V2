# AgriWater Optimizer V2

**Systeme d'optimisation energetique pour l'irrigation agricole au Sahel**

Evolution full-stack de [agriwater-optimizer](https://github.com/Abdoul202/agriwater-optimizer) : un backend Python (FastAPI + solveur MILP) et un frontend React moderne, concus pour minimiser les couts energetiques des pompes d'irrigation dans le contexte du Burkina Faso.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    agriwater-optimizer-V2                    │
│                                                             │
│  ┌──────────────────────┐    ┌───────────────────────────┐  │
│  │       Backend        │    │        Frontend           │  │
│  │                      │    │                           │  │
│  │  FastAPI REST API    │◄──►│  React 19 + TypeScript    │  │
│  │  PuLP/CBC (MILP)     │    │  Vite + Tailwind CSS     │  │
│  │  Open-Meteo API      │    │  Recharts                │  │
│  │  Pydantic            │    │  React Router            │  │
│  │                      │    │                           │  │
│  │  Python 3.10+        │    │  Node 18+                │  │
│  └──────────────────────┘    └───────────────────────────┘  │
│         :8000                         :5173                 │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
uvicorn api.main:app --reload
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Pages du dashboard

| Page | Description |
|------|-------------|
| **Tableau de bord** | 8 KPIs en temps reel, cout optimise vs baseline, heatmap pompes 24h, solaire vs demande, niveau reservoir |
| **Optimisation** | Sliders interactifs (surface, pompes, tarifs, ET0, solaire, reservoir), lancement MILP en temps reel, projections, planning detaille |
| **Meteo** | Previsions 7 jours Open-Meteo, risque de secheresse, evapotranspiration ET0, historique 30 jours, recommandation irrigation |
| **Configuration** | Specs pompes avec degradation, tarifs SONABEL, cultures avec coefficients kc, architecture systeme |

## API Endpoints

| Methode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/optimize` | Lance l'optimisation MILP avec parametres ajustables |
| `GET` | `/api/weather/forecast?days=7` | Previsions meteo + indice de secheresse |
| `GET` | `/api/weather/history?days_back=30` | Historique meteo |
| `GET` | `/api/config/demo` | Configuration ferme demo (pompes, cultures, tarifs) |
| `GET` | `/api/health` | Health check |

## Moteur d'optimisation MILP

Le solveur minimise le cout total sur 24 heures :

```
min Σ(h=0..23) [
    Σ(p) x[p][h] * puissance_reelle[p] * tarif[h]     ← cout energie
  + penalite[h]                                         ← depassement puissance souscrite
  + Σ(p) demarrage[p][h] * 5000                         ← usure equipements
  - economies_solaire[h]                                ← offset photovoltaique
]
```

**Contraintes :**
- Demande en eau horaire satisfaite (profil sahelien : pics matin 5-8h + soir 18-21h)
- Penalite 200 FCFA/kW au-dessus de 150 kW souscrits (SONABEL)
- Detection demarrages : `demarrage[p][h] >= x[p][h] - x[p][h-1]`
- Maximum 8 demarrages par pompe par jour
- Maximum 20 heures de fonctionnement par pompe par jour
- Puissance reelle : `(puissance / efficacite) * (1 + age * 0.02)`

## Specs pompes (alignees sur le depot original)

| Pompe | Debit | Puissance | Efficacite | Age | Puissance reelle | Type |
|-------|-------|-----------|------------|-----|------------------|------|
| P1 | 60 m3/h | 45 kW | 0.75 | 5 ans | 66.0 kW | principale |
| P2 | 50 m3/h | 38 kW | 0.72 | 8 ans | 61.2 kW | secondaire |
| P3 | 55 m3/h | 42 kW | 0.73 | 3 ans | 61.0 kW | appoint |

## Ameliorations vs depot original

| Original (`agriwater-optimizer`) | V2 (ce depot) |
|----------------------------------|---------------|
| Script console + matplotlib | Backend API + Frontend React |
| Demande en eau fixe | Demande dynamique basee sur ET0 |
| Valeurs pompes en dur | Config chargeable JSON (`FarmConfig.from_json()`) |
| Pas de gestion reservoir | Suivi niveaux de reservoir heure par heure |
| Pas de meteo | Open-Meteo : previsions 7j, historique 30j, secheresse |
| Horizon 24h fixe | Profils saisonniers (seche x1.35, pluies x0.60) |
| Parametres non ajustables | Sliders interactifs pour tous les parametres |
| Pas de tests | 25 tests unitaires pytest |

## Contexte Burkina Faso

- **Tarifs SONABEL** : heures pleines 7h-23h (110 FCFA/kWh), creuses (75 FCFA/kWh)
- **Puissance souscrite** : 150 kW, penalite 200 FCFA/kW depasse
- **Cultures** : mil, sorgho, mais, niebe, maraichage (coefficients kc)
- **Saisons** : seche (nov-avr, demande x1.35), pluies (jun-sep, x0.60), transition (x0.85)
- **Solaire** : irradiation excellente au Sahel (5-7 kWh/m2/jour)
- **Monnaie** : FCFA (franc CFA ouest-africain)

## Structure du projet

```
agriwater-optimizer-V2/
├── backend/                  # API Python + moteur MILP
│   ├── agriwater/            # Package optimisation
│   │   ├── optimizer/        # engine.py + models.py
│   │   ├── weather/          # forecast.py (Open-Meteo)
│   │   ├── data/             # generator.py (demo + solaire)
│   │   └── config.py         # Settings Pydantic
│   ├── api/                  # FastAPI REST
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── routes/
│   ├── tests/                # 25 tests pytest
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                 # React + Vite + Tailwind
│   └── src/
│       ├── pages/            # Dashboard, Optimizer, Weather, Config
│       ├── components/       # Charts, MetricCard, Sidebar
│       └── lib/              # API client, formatters
├── .gitignore
└── README.md
```

## Roadmap

- [x] **v1.0** - Moteur MILP original (console + matplotlib)
- [x] **v2.0** - Full-stack React + FastAPI, ET0 dynamique, demarrages, reservoir, 25 tests
- [ ] **v2.1** - Multi-jours (optimisation sur 7 jours), export PDF
- [ ] **v2.2** - Prediction ML du besoin en eau (scikit-learn)
- [ ] **v3.0** - App mobile Flutter + alertes SMS

## Auteur

**OUEDRAOGO Abdoulaye** - [GitHub](https://github.com/Abdoul202)

## Licence

MIT
