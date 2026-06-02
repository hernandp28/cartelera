# Motor predictivo — roadmap

Implementación actual: `app/services/prediction_service.py` (modelo **dummy**
determinístico, interfaz `predict(match)` estable).

## Modelo híbrido objetivo
1. **Base estadística** — Elo + ranking FIFA + forma reciente + **Poisson** para goles.
2. **ML 1X2** — LightGBM/XGBoost sobre dataset histórico internacional.
3. **Capa contextual** — ajusta probabilidades por lesiones, sanciones, descanso,
   sede, clima, actualidad (noticias), cambios tácticos.
4. **Capa explicativa** — genera texto claro con factores +/–.

## Variables (mínimas)
Elo, ranking FIFA, últimos 5/10/20, GF, GC, DG, xG/xGA, rendimiento vs nivel
similar, importancia, sede, descanso, viaje, lesiones clave, sanciones, ánimo
(noticias), cambio de DT, alineación probable, odds (señal secundaria).

## Backtesting
`accuracy`, `log loss`, `Brier score`, calibración. Guardar cada predicción
antes del partido (tabla `predictions` + `model_versions`) para auditoría.

Archivos a crear: `features.py`, `elo.py`, `poisson.py`, `train.py`,
`backtest.py`, `registry.py`.
