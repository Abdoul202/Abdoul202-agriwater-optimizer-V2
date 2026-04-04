# AgriWater Optimizer V2 - Backend

API REST Python pour l'optimisation energetique de l'irrigation agricole au Sahel.

## Stack

- **FastAPI** - API REST async
- **PuLP + CBC** - Solveur MILP (programmation lineaire mixte)
- **Pydantic** - Validation et serialisation des donnees
- **httpx** - Client HTTP pour Open-Meteo
- **pytest** - 25 tests unitaires

## Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

Copier `.env.example` vers `.env` et ajuster si besoin :

```bash
cp .env.example .env
```

Variables disponibles :

| Variable | Default | Description |
|----------|---------|-------------|
| `FARM_LATITUDE` | 12.37 | Latitude (Ouagadougou) |
| `FARM_LONGITUDE` | -1.52 | Longitude |
| `FARM_NAME` | Ferme Demo Ouagadougou | Nom de la ferme |
| `TARIFF_PEAK` | 110 | Tarif heures pleines (FCFA/kWh) |
| `TARIFF_OFFPEAK` | 75 | Tarif heures creuses (FCFA/kWh) |
| `PEAK_HOURS_START` | 7 | Debut heures pleines |
| `PEAK_HOURS_END` | 23 | Fin heures pleines |
| `SUBSCRIBED_POWER_KW` | 150 | Puissance souscrite SONABEL |
| `PENALTY_RATE_FCFA` | 200 | Penalite par kW depasse |

## Lancement

```bash
uvicorn api.main:app --reload
```

L'API est disponible sur `http://localhost:8000`.  
La documentation Swagger est sur `http://localhost:8000/docs`.

## API Endpoints

### `POST /api/optimize`

Lance l'optimisation MILP avec parametres ajustables.

**Body (JSON) :**
```json
{
  "area_ha": 30,
  "num_pumps": 3,
  "subscribed_power_kw": 150,
  "penalty_rate_fcfa": 200,
  "tariff_peak": 110,
  "tariff_offpeak": 75,
  "peak_start": 7,
  "peak_end": 23,
  "solar_capacity_kw": 10,
  "cloud_factor": 0.1,
  "reservoir_m3": 500,
  "et0_mm": null
}
```

**Reponse :** Planning optimal 24h avec couts, schedule pompes, niveaux reservoir, comparaison baseline.

### `GET /api/weather/forecast?days=7`

Previsions meteo via Open-Meteo + indice de risque de secheresse.

### `GET /api/weather/history?days_back=30`

Historique meteo (temperatures, precipitations, ET0).

### `GET /api/config/demo`

Configuration ferme demo avec specs pompes, cultures et tarifs.

### `GET /api/health`

Health check.

## Tests

```bash
pytest tests/ -v
```

```
tests/test_generator.py    11 tests  - Config demo, pompes, tarifs, solaire, saisonnier
tests/test_optimizer.py    11 tests  - MILP, savings, startups, ET0, reservoir
tests/test_weather.py       4 tests  - Risque secheresse (offline)
                           --------
                           25 tests
```

## Moteur MILP

### Fonction objectif

```
min Σ(h) [ Σ(p) x[p][h] * actual_power[p] * tarif[h]
         + penalty[h]
         + Σ(p) startup[p][h] * 5000
         - solar_savings[h] ]
```

### Variables de decision

| Variable | Type | Description |
|----------|------|-------------|
| `x[p][h]` | Binaire | Pompe p active a l'heure h |
| `startup[p][h]` | Binaire | Pompe p demarre a l'heure h |
| `total_power[h]` | Continue | Puissance totale a l'heure h |
| `penalty[h]` | Continue | Penalite de depassement a l'heure h |

### Contraintes

1. **Demande en eau** : `Σ(p) x[p][h] * debit[p] >= demande[h]`
2. **Puissance totale** : `total_power[h] = Σ(p) x[p][h] * actual_power[p]`
3. **Penalite** : `penalty[h] >= 200 * (total_power[h] - 150)`
4. **Detection demarrage** : `startup[p][h] >= x[p][h] - x[p][h-1]`
5. **Max demarrages** : `Σ(h) startup[p][h] <= 8` par pompe
6. **Max heures** : `Σ(h) x[p][h] <= 20` par pompe

### Puissance reelle

Prend en compte l'efficacite et la degradation liee a l'age :

```
actual_power = (power_kw / efficiency) * (1 + age_years * 0.02)
```

| Pompe | Nominale | Reelle | Degradation |
|-------|----------|--------|-------------|
| P1 (5 ans) | 45 kW | 66.0 kW | +46.7% |
| P2 (8 ans) | 38 kW | 61.2 kW | +61.1% |
| P3 (3 ans) | 42 kW | 61.0 kW | +45.2% |

## Structure

```
backend/
├── agriwater/
│   ├── __init__.py
│   ├── config.py              # Pydantic settings (.env)
│   ├── optimizer/
│   │   ├── engine.py          # Moteur MILP (startup, penalty, reservoir)
│   │   └── models.py          # Pump, Crop, FarmConfig, Result, JSON I/O
│   ├── weather/
│   │   └── forecast.py        # Open-Meteo API + risque secheresse
│   └── data/
│       └── generator.py       # Config demo + solaire + saisonnier
├── api/
│   ├── main.py                # FastAPI app + CORS
│   ├── schemas.py             # Request/Response Pydantic models
│   └── routes/
│       ├── optimize.py        # POST /api/optimize
│       ├── weather.py         # GET /api/weather/*
│       └── config.py          # GET /api/config/demo
├── tests/
│   ├── test_optimizer.py
│   ├── test_generator.py
│   └── test_weather.py
├── .env.example
├── pyproject.toml
└── requirements.txt
```
