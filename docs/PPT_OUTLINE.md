# Presentation Deck Outline (map to judging criteria)

1. Title + team + problem statement chosen (#5, Urban AQI Intelligence)
2. Problem context (cite the CPCB/Lancet stats from the problem PDF)
3. Why existing tools fail (dashboards without attribution/enforcement/forecast)
4. Architecture diagram (docs/ARCHITECTURE.md)
5. Data: real Pune CAAQMS data + transparently-labeled synthetic multi-city
   simulation for scalability demo
6. Forecasting: model comparison table (backend/model_comparison.py output) -
   show RMSE vs persistence baseline, state improvement %
7. Source attribution: explainable pollutant-ratio logic + example output
8. Enforcement prioritization: ranked table, explain scoring formula
9. Citizen advisory: live demo, multi-language via LLM rewrite
10. Live demo (dashboard walkthrough)
11. Scalability: swap synthetic loader for real CAAQMS API per city
12. Limitations + next steps (real ground-truth attribution validation,
    population-density weighted exposure, live CAAQMS feed integration)
