# AgriWater Optimizer V2 - Frontend

Dashboard React pour la visualisation et le pilotage interactif de l'optimisation d'irrigation.

## Stack

- **React 19** + TypeScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling (dark theme)
- **Recharts** - Graphiques interactifs (barres, aires, lignes)
- **React Router** - Navigation SPA
- **Lucide React** - Icones

## Installation

```bash
cd frontend
npm install
```

## Lancement

```bash
npm run dev
# → http://localhost:5173
```

Le proxy Vite redirige automatiquement `/api/*` vers `http://localhost:8000` (backend FastAPI).

## Build production

```bash
npm run build    # TypeScript check + bundle dans dist/
npm run preview  # Preview du build
```

## Pages

### Tableau de bord (`/`)

Page d'accueil avec vue d'ensemble automatique :
- **8 KPIs** : cout optimise, economies, eau pompee, penalites, energie, demarrages, puissance max, baseline
- **Cout horaire** : graphique barres optimise vs baseline (24h)
- **Solaire vs Demande** : graphique aires production solaire vs consommation pompes
- **Heatmap pompes** : grille 24h montrant l'activation de chaque pompe
- **Reservoir** : graphique aire du niveau d'eau heure par heure

### Optimisation interactive (`/optimizer`)

Panneau de controle avec sliders pour ajuster en temps reel :
- **Ferme** : surface (ha), nombre de pompes, puissance souscrite, reservoir
- **Tarifs SONABEL** : heures pleines, heures creuses, penalite depassement
- **Solaire & Meteo** : capacite PV, couverture nuageuse, ET0 dynamique
- **Resultats** : 8 KPIs, charts, planning detaille, projections mensuelles/annuelles, ROI solaire

### Meteo (`/weather`)

Donnees meteo en temps reel via l'API Open-Meteo :
- Banniere de risque de secheresse (faible/modere/eleve/severe)
- Previsions 7 jours (temperature, precipitation, ET0)
- Recommandation irrigation basee sur le bilan hydrique
- Historique 30 jours avec tendances ET0

### Configuration (`/config`)

Affichage des specs du systeme :
- Tarifs SONABEL avec plages horaires
- Specs pompes : debit, puissance, efficacite, age, degradation, cout demarrage
- Cultures : surface, besoin eau, coefficient kc, priorite
- Schema d'architecture du systeme

## Communication avec le backend

Le client API (`src/lib/api.ts`) expose 4 fonctions :

```typescript
runOptimization(params)  // POST /api/optimize
getForecast(days)        // GET  /api/weather/forecast
getHistory(daysBack)     // GET  /api/weather/history
getDemoConfig()          // GET  /api/config/demo
```

Les types TypeScript sont synchronises avec les schemas Pydantic du backend.

## Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts           # Proxy /api → localhost:8000
├── tsconfig.json
└── src/
    ├── main.tsx             # Point d'entree
    ├── App.tsx              # Router (4 routes)
    ├── index.css            # Tailwind + dark theme
    ├── lib/
    │   ├── api.ts           # Client API + types TypeScript
    │   └── format.ts        # Formatters (FCFA, decimales)
    ├── components/
    │   ├── Sidebar.tsx      # Navigation laterale
    │   ├── MetricCard.tsx   # Carte KPI reutilisable
    │   └── Charts.tsx       # 6 composants Recharts
    └── pages/
        ├── Dashboard.tsx    # Tableau de bord
        ├── Optimizer.tsx    # Optimisation interactive
        ├── Weather.tsx      # Meteo + secheresse
        └── Config.tsx       # Configuration systeme
```

## Composants graphiques

| Composant | Type | Utilisation |
|-----------|------|-------------|
| `CostComparisonChart` | BarChart | Cout optimise vs baseline (24h) |
| `SolarDemandChart` | AreaChart | Production solaire vs demande pompes |
| `PumpScheduleChart` | Grille CSS | Heatmap activation pompes 24h |
| `ReservoirChart` | AreaChart | Niveau reservoir heure par heure |
| `WeatherChart` | ComposedChart | Temperature + precipitation (7j) |
| `ET0Chart` | ComposedChart | Evapotranspiration vs precipitation |
